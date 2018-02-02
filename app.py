import os
import time
import requests
import random

from requests import post

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, FollowEvent, UnfollowEvent, JoinEvent, LeaveEvent, PostbackEvent,
    TextMessage, StickerMessage, ImageMessage, TextSendMessage,ImageSendMessage,
    ImageCarouselColumn,ImageCarouselTemplate,TemplateSendMessage,
    MessageTemplateAction,URITemplateAction,PostbackTemplateAction,
)
from imgurpython import ImgurClient
from airtable import Airtable

app = Flask(__name__)
bot_id = os.environ.get('bot_id', None)
handler = WebhookHandler(os.environ.get('ChannelSecret'))
bot = LineBotApi(os.environ.get('ChannelAccessToken'))
server_url = os.environ.get('server_url')
airtable = Airtable(os.environ.get('base_key'), os.environ.get('table_name'),os.environ['AIRTABLE_API_KEY'])
imgCarouseltable = Airtable(os.environ.get('base_key'), os.environ.get('table_name_imgCarousel'),os.environ['AIRTABLE_API_KEY'])
passList = Airtable(os.environ.get('base_key'), os.environ.get('table_name_PassList'),os.environ['AIRTABLE_API_KEY'])
imgur = None


def _post(endpoint, **json):
    try:
        print(endpoint)
        print('debug [%s]' % (json))
        #r = requests.post(server_url + endpoint, json=json, timeout=30)
        
        #print('debug [%s] [%s]' % (r.status_code, json['message'])) #用來檢測heroku沒有將內容傳送過來的問題 ...吃字
        #return r
    except:
        pass

def get_id(event):
    if   event.source.type == 'user':
        return {'bot_id':bot_id, 'user_id':event.source.user_id, 'group_id':None}
    elif event.source.type == 'group':
        return {'bot_id':bot_id, 'user_id':event.source.user_id, 'group_id':event.source.group_id}
    elif event.source.type == 'room':
        return {'bot_id':bot_id, 'user_id':event.source.user_id, 'group_id':event.source.room_id}


@app.route("/callback", methods=['POST'])
def callback():
    print('test 1111') 
    #print(request) 
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def MatchAction(push_id,matchData,Smsg='',UserName=''):
    print(matchData)
    if matchData['fields']['Type'] == 'image':
        Images = matchData['fields']['image']
        for imgdata in Images:
            image = imgdata['url']
            bot.push_message(push_id,ImageSendMessage(original_content_url=image,preview_image_url=image))
    elif matchData['fields']['Type'] == 'imageRandom':
        Images = matchData['fields']['image']
        idx = random.randrange(0,len(Images))
        image = Images[idx]['url']
        bot.push_message(push_id,ImageSendMessage(original_content_url=image,preview_image_url=image))
    elif matchData['fields']['Type'] == 'text':
        msg = matchData['fields']['text'].replace('%name',UserName)
        bot.push_message(push_id,TextSendMessage(text=msg))
    elif matchData['fields']['Type'] == 'textRandom':
        msgs = matchData['fields']['text'].split('%s')
        idx = random.randrange(0,len(msgs))
        msg = msgs[idx].replace('%name',UserName)
        bot.push_message(push_id,TextSendMessage(text=msg))
    elif matchData['fields']['Type'] == 'funcS':
        msg = matchData['fields']['text'].replace('%s',Smsg)
        msg = msg.replace('%name',UserName)
        bot.push_message(push_id,TextSendMessage(text=msg))
    elif matchData['fields']['Type'] == 'ImgCarousel':
        ImgCar_Ids = matchData['fields']['ImgCarousel']
        ImgCarouselCols = []
        for imgC_Id in ImgCar_Ids:
            imgCar = imgCarouseltable.get(imgC_Id)
            if imgCar['fields']['Type'] == 'message':
                ImgCarouselCols.append(ImageCarouselColumn(image_url=imgCar['fields']['ImageUrl'][0]['url'],action=MessageTemplateAction(label=imgCar['fields']['label'],text=imgCar['fields']['text'])))
            elif imgCar['fields']['Type'] == 'uri':
                ImgCarouselCols.append(ImageCarouselColumn(image_url=imgCar['fields']['ImageUrl'][0]['url'],action=URITemplateAction(label=imgCar['fields']['label'],uri=imgCar['fields']['uri'])))
            elif imgCar['fields']['Type'] == 'postback':
                ImgCarouselCols.append(ImageCarouselColumn(image_url=imgCar['fields']['ImageUrl'][0]['url'],action=PostbackTemplateAction(label=imgCar['fields']['label'],text=imgCar['fields']['text'],data=imgCar['fields']['data'])))
        bot.push_message(push_id,TemplateSendMessage(alt_text=matchData['fields']['text'].replace('%name',UserName) ,template=ImageCarouselTemplate(columns=ImgCarouselCols)))

    evnetTime = time.gmtime()
    etString =time.strftime("%Y-%m-%dT%H:%M:%S.000Z", evnetTime)
    fields = {"eventCount": matchData['fields']['eventCount']+1,"eventTime":etString}
    airtable.update(matchData['id'], fields)  
    # fields = {'evnetTime':evnetTime}
    # print(fields)
    # airtable.update(matchData['id'], fields)     


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event) 
    #r = _post('/text', **get_id(event), message=event.message.text, reply_token=event.reply_token)
    push_id = ''
    hasUserData = False
    userdata = []
    if  event.source.type == 'user':
        push_id = event.source.user_id
        userdata = bot.get_profile(user_id=event.source.user_id)
        hasUserData = True
    elif event.source.type == 'group':
        push_id = event.source.group_id
        if event.source.user_id is None:
            userdata = bot.get_group_member_profile(group_id=event.source.group_id,user_id=event.source.user_id)
            hasUserData = True
    elif event.source.type == 'room':
        push_id = event.source.room_id
        if event.source.user_id is None:
            userdata = bot.get_room_member_profile(room_id=event.source.room_id,user_id=event.source.user_id)
            hasUserData = True
    event_msg = event.message.text
         
    passUser = passList.match('UserId',userdata.user_id)    

    msg = ''
    image = ''
    UserName = ''
    if hasUserData :
        UserName =userdata.display_name
    #print(airtable.match('Key',msg))
    matchData = airtable.match('Key',event_msg)
    if 'id' not in matchData:
        if 'id' in passUser:
            print('pass')
            print(userdata)
            return
        includeCount = 0
        
        matchData = airtable.search('Type','funcS',sort='CreateTime')
        for record in matchData:
            rKeys = record['fields']['Key'].split('%s')
            start_idx = -1
            end_idx = -1
            if len(rKeys) > 1:
                start_idx = event_msg.find(rKeys[0]) + len(rKeys[0])
                end_idx = event_msg.find(rKeys[1],start_idx)
            if start_idx > -1 and end_idx>start_idx:
                Smsg = event_msg[start_idx:end_idx]
                MatchAction(push_id,record,Smsg,UserName)
                includeCount = includeCount+1
        
        matchData = airtable.search('rule','include',sort='CreateTime')
        
        if includeCount==0:
            for record in matchData:
                rKey = record['fields']['Key']
                if event_msg.find(rKey) > -1 :
                    MatchAction(push_id,record,UserName=UserName)
        
        #print(matchData) 
    else:
        
        if matchData['fields']['Type'] == 'passOff':
            if hasUserData :
                msg = matchData['fields']['text'].replace('%name',UserName)
                bot.push_message(push_id,TextSendMessage(text=msg))
                if 'id' in passUser:
                    passList.delete(passUser['id'])
                return
        if 'id' in passUser:
            print('pass Name:'+UserName+' UserId:'+userdata.user_id)
            return
        
        if matchData['fields']['Type'] == 'passOn':
            if hasUserData :
                msg = matchData['fields']['text'].replace('%name',UserName)
                bot.push_message(push_id,TextSendMessage(text=msg))
                fields = {"Name": userdata.display_name,"UserId":userdata.user_id,"Image":[{"url":userdata.picture_url}]}
                passList.insert(fields)
            return

        #print(matchData)
        MatchAction(push_id,matchData,UserName=UserName)
        # if matchData['fields']['Type'] == 'image':
            # Images = matchData['fields']['image']
            # for imgdata in Images:
                # image = imgdata['url']
                # bot.push_message(push_id,ImageSendMessage(original_content_url=image,preview_image_url=image))
            # #image = matchData['fields']['image'][0]['url']
            # #bot.push_message(push_id,ImageSendMessage(original_content_url=image,preview_image_url=image))
        # elif matchData['fields']['Type'] == 'text':
            # msg = matchData['fields']['text']
            # bot.push_message(push_id,TextSendMessage(text=msg))
    
    #bot.reply_message(event.reply_token, TextSendMessage(text=msg))
    #bot.push_message(push_id,TextSendMessage(text=msg))
    
    ##bot.reply_message(event.reply_token, ImageMessage(original_content_url=image,preview_image_url=image))


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    _post('/sticker', **get_id(event))


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    _post('/image', **get_id(event))
    #print(event) 
    # def get_imgur_client():
        # global imgur
        # if imgur is None:
            # try:
                # return ImgurClient(os.environ.get('imgur_id'), os.environ.get('imgur_secret'))
            # except:
                # return None
        # return None

    # if event.source.type == 'user':
        # path = '%s.tmp' % event.message.id
        # message_content = bot.get_message_content(event.message.id)
        # with open(path, 'wb') as f:
            # for chunk in message_content.iter_content():
                # f.write(chunk)
        # imgur = get_imgur_client()
        # if imgur is None:
            # msg = '圖床目前無法訪問'
        # else:
            # for i in range(100):
                # try:
                    # image = imgur.upload_from_path(path)
                    # msg = image['link']
                    # break
                # except Exception as e:
                    # msg = '上傳圖片錯誤了...\n%s' % str(e)
                    # time.sleep(0.2)
        # os.remove(path)
        # bot.reply_message(event.reply_token, TextSendMessage(text=msg))


@handler.add(FollowEvent)
def follow(event):
    _post('/follow', **get_id(event), reply_token=event.reply_token)

@handler.add(UnfollowEvent)
def unfollow(event):
    _post('/unfollow', **get_id(event))

@handler.add(JoinEvent)
def join(event):
    _post('/join', **get_id(event), reply_token=event.reply_token)

@handler.add(LeaveEvent)
def leave(event):
    _post('/leave', **get_id(event))

@handler.add(PostbackEvent)
def postback(event):
    _post('/postback', **get_id(event))
    print(event)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print('bot start') 
    app.run(host='0.0.0.0', port=port, threaded=True)
    
