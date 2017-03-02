#!/usr/bin/python
# -*- coding: utf-8

"""
    Web Kassa IceRest 1.0
    License GPL
    writed by Romanenko Ruslan
    redeyser@gmail.com
"""

from   BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from   SocketServer import ThreadingMixIn
from   fhtml import *
from   md5 import md5
from clientDrv import DTPclient
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import threading
import urlparse
import cgi
import Cookie
import time
import sys,os
import re
import json
import subprocess
PIPE = subprocess.PIPE
import my
import math
from dbIceRest import *

MYSQL_HOST  = 'localhost'
VERSION     = '1.0.002'

_RESULT         = 'result'
_ID             = 'id'

POST_TRUE       = "1"
POST_FALSE      = "0"

icelock=threading.Lock()

def ice_lock():
    icelock.acquire()

def ice_unlock():
    icelock.release()

def _verify_EAN(shk):
    if len(shk)<13:
        #return False
        shk=shk.rjust(13,"0")
    s1=0
    for i in range(2,len(shk),2):
        s1+=int(shk[i-1])
    s2=0
    for i in range(1,len(shk),2):
        s2+=int(shk[i-1])
    r=(s1*3+s2)%10
    if r!=0:
        r=10-r
    if r==int(shk[-1]):
        return True
    else:
        print r,int(shk[-1])
        return False

def isprefix(prefix,shk):
    a=prefix.split(";")
    pref=shk[:len(prefix)]
    if pref in a:
        return True
    else:
        return False

class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
            return

    def mysql_open(self):
        self.db = dbIceRest(DATABASE, MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD) 
        return self.db.open()
        
    def _getval(self,key,default):
        if self.get_vals.has_key(key):
            return self.get_vals[key]
        else:
            return default

    def _send_HEAD(self,tp,code=200):
        self.send_response(code)
        self.send_header("Content-type", tp)
        self.end_headers()

    def _send_redirect(self,url):
        self.send_response(302)
        self.send_header('Location', url)

    def _redirect(self,url):
        self._send_redirect(url)
        self.end_headers()

    def do_HEAD(self):
        self._send_HEAD('text/html')
        self.send_response(200)

    def ReadCookie(self):
        if "Cookie" in self.headers:
            c = Cookie.SimpleCookie(self.headers["Cookie"])
            if c.has_key('IceRestlogin') and c.has_key('IceRestpassword'):
                self.curlogin    = c['IceRestlogin'].value
                self.curpassword = c['IceRestpassword'].value
                return True
            else:
                self.curlogin    = None
                self.curpassword = None
                return False

    def WriteCookie(self,vals):
        if vals.has_key("login"):
            c = Cookie.SimpleCookie()
            c['IceRestlogin'] = vals["login"]
            c['IceRestpassword'] = vals["password"]
            self.send_header('Set-Cookie', c.output(header=''))

    def ClearCookie(self):
        c = Cookie.SimpleCookie()
        c['IceRestlogin'] = ""
        c['IceRestpassword'] = ""
        self.send_header('Set-Cookie', c.output(header=''))

    def GetAuth(self,gets):
        if gets.has_key("_user") and gets.has_key("_password"):
            self.curlogin    = gets['_user']
            self.curpassword = gets['_password']
            return True
        else:
            return False
            
    def PostAuth(self,form):
        if form.has_key("_user") and form.has_key("_password"):
            self.curlogin    = form['_user'].value
            self.curpassword = form['_password'].value
            return True
        else:
            return False

    def get_file(self,path="",decode=True):
        if path[0]!='/':
            path='/'+path
        path='site'+path
        try:
            f=open(path,"r")
            message=f.read()
            f.close()
        except:
            message=''
        if decode:
            message=message.decode("utf8")
        return message

    def put_file(self,filedata,path):
        path='site'+path
        try:
            f=open(path,"w")
            f.write(filedata)
            f.close()
            return True
        except:
            return False
            pass
        return 
    
    def pattern_params_get(self,html):
        params={}
        a=re.findall("%%#.*?#.*?%%",html)
        for n in a:
            m=re.search("%%#(.*?)#(.*?)%%",n)
            if m!=None and len(m.groups())==2:
                tag=m.group(1)
                params[tag]=m.group(2)
        return params

    def pattern_rep_arr(self,html,amark,aval):
        return ht_reptags_arr(html,amark,aval)

    def pattern_rep_hash(self,html,h):
        return ht_reptags_hash(html,h)

    def pattern_params_clear(self,html):
        a=re.findall("%%#.*?#.*?%%",html)
        for n in a:
            html=html.replace(n,"")
        a=re.findall("%.*?%",html)
        for n in a:
            html=html.replace(n,"")
        return html

    def _write(self,html):
        self.wfile.write(html.encode("utf8"))

    def write_file(self,f):
        self._send_HEAD("application/x")
        html=self.get_file(f,False)
        self.wfile.write(html)

    def wbody(self,p):
        b=self.get_file(p)
        self._send_HEAD("text/html")
        html=self.get_file('/head.html')
        info_ip=self.client_address[0]
        html = ht_reptags_arr(html,["%css%","%body%"],[self.cur_css,b])
        html = ht_reptags_arr(html,["%version%","%info_ip%"],[VERSION,info_ip])
        self._write(html)

    def wbodyh(self,b):
        self._send_HEAD("text/html")
        html=self.get_file('/head.html')
        info_ip=self.client_address[0]
        html = ht_reptags_arr(html,["%css%","%body%"],[self.cur_css,b])
        html = ht_reptags_arr(html,["%version%","%info_ip%"],[VERSION,info_ip])
        self._write(html)

    def wjson(self,j):
        self._send_HEAD("application/json")
        self._write(j)

    def verify(self):   
        if self.db._user_auth(self.curlogin,self.curpassword):
            if self.db.user['css']!='':
                self.cur_css=self.db.user['css']
            self.currule=self.db.user['type']
            self.iduser=self.db.user['id']
            return True
        else:
            return False

    def return_false(self):
        j=json.dumps({_RESULT:False})
        self.wjson(j)

    def return_true(self):
        j=json.dumps({_RESULT:True})
        self.wjson(j)

    def qstd_gets(self,table,where="",fields=None,order=None,tohash=False,toarr=False,usegets=False):
        if usegets:
            data=self.db._gets( table )
        else:
            data=self.db._select(table,where=where,fields=fields,order=order,tohash=tohash,toarr=toarr)
        j=json.dumps({_RESULT:True,'data':data},ensure_ascii=False)
        self.wjson(j)
        return True

    def qstd_getid(self,table,fid="id"):
        id=self._getval('id',None)
        if id==None:
            self.return_false()
            return False
        if int(id)==0:
            data=self.db._empty( table )
        else:
            data=self.db._select( table, "%s=%s" % (fid,id) )
            data=data[0]
        j=json.dumps({_RESULT:True,'data':data},ensure_ascii=False)
        self.wjson(j)
        return True

    def qstd_putid(self,table,fid="id"):
        if not self.form.has_key("data"):
            self.return_false()
            return False
        data=json.loads(self.form["data"].value)
        if data['id']==0:
            del data['id']
            r=self.db._insert( table, data )
            id=self.db.lastid
        else:
            r=self.db._update( table, data, "%s=%s" % (fid,data['id']) )
            id=data['id']
        j=json.dumps({_RESULT:r,_ID:id})
        self.wjson(j)
        return True

    def qstd_delid(self,table,fid="id"):
        if not self.form.has_key("data"):
            self.return_false()
            return False
        data=json.loads(self.form["data"].value)
        r=self.db._delete( table, "id=%s" % data['id'] )
        j=json.dumps({_RESULT:r})
        self.wjson(j)
        return True

    def create_dtp(self):
        self.dtpclient=DTPclient(self.db.sets["dtprint_ip"],int(self.db.sets["dtprint_port"]),self.db.sets["dtprint_passwd"])
        if self.db.sets.has_key('d_ignore') and self.db.sets['d_ignore']=='1':
            self.dtpclient.err_ignore=True
        else:
            self.dtpclient.err_ignore=False
        if self.db.sets.has_key('d_autocut') and self.db.sets['d_autocut']=='1':
            self.dtpclient.use_cut=True
        else:
            self.dtpclient.use_cut=False

    def do_GET(self):

        self.cur_css='gray.css'
        parsed_path = urlparse.urlparse(self.path)
        getvals=parsed_path.query.split('&')
        self.get_vals={}

        try:
            for s in getvals:
                if s.find('=')!=-1:
                    (key,val) = s.split('=')
                    self.get_vals[key] = val
        except:
            print "error get!"
            self.get_vals={}
                

        if self.path.find(".woff")!=-1:
            self._send_HEAD("application/x-font-woff",200)
            message=self.get_file(self.path)
            self._write(message)
            return
        if self.path.find(".js")!=-1:
            self._send_HEAD("text/javascript",200)
            message=self.get_file(self.path)
            self._write(message)
            return
        if self.path.find(".css")!=-1:
            self._send_HEAD("text/css",200)
            message=self.get_file(self.path)
            self._write(message)
            return
        if (self.path.find(".png")!=-1)or(self.path.find(".gif")!=-1)or(self.path.find(".jpg")!=-1):
            self._send_HEAD("image/png",200)
            message=self.get_file(self.path,decode=False)
            self.wfile.write(message)
            return

        if not self.mysql_open():
            self._send_HEAD("text/html",404)
            return
        else:
            self.db.sets_read()


        """ GET SIMPLE REQUEST
            ------------------
        """    
        if self.path=='/':
            self.wbody("/index.html")
            return

        if self.path=='/order':
            self.wbody("/order.html")
            return

        if self.path.find("/template/")!=-1:
            h=self.get_file(self.path)
            self._send_HEAD("text/html")
            self._write(h)
            return

        if parsed_path.path=='/zakaz/list':
            
            d=self.db._select(TB_BOXES_HD,  where='status>0',\
                                            order='status desc,dt,tm',\
                                            fields=["id","idhd","status","dt","tm"])
            z={}
            order=[]
            for r in d:
                id=r['id']
                idhd=r['idhd']
                if idhd==0:
                    idz=id
                else:
                    idz=idhd
                if not z.has_key(idz):
                    z[idz]={'boxes':[],'dt':r['dt'],'tm':r['tm'],'status':r['status'],'count':0}
                    order.append(idz)
                z[idz]['boxes'].append({'id':id,'status':r['status']})
                z[idz]['count']=z[idz]['count']+1
                if r['status']<z[idz]['status']:
                    z[idz]['status']=r['status']
            Z=[]
            for idz in order:
                z[idz].update({'id':idz})
                Z.append(z[idz])
            for i in range(len(Z)-1):
                for v in range(len(Z)-1):
                    if Z[v]['status']<Z[v+1]['status']:
                        t=Z[v]
                        Z[v]=Z[v+1]
                        Z[v+1]=t
            j=json.dumps(Z)
            self.wjson(j)
            return

        """ AUTHORIZATION
            ------------------
        """    
        if self.path.find("/login")!=-1:
            self._send_redirect("/boxes")
            self.WriteCookie(self.get_vals)
            self.end_headers()
            return

        if parsed_path.path=='/users/gets':
            users=self.db._gets(TB_USERS)
            j=json.dumps(users,ensure_ascii=False)
            self.wjson(j)
            return

        if not self.ReadCookie():
            if not self.GetAuth(self.get_vals):
                self._redirect("/")
                return

        self.GetAuth(self.get_vals)

        if not self.verify():
            self._redirect("/")
            print "not verify"
            return

        if (self.path.find("/unlogin")==0):
            self._send_redirect("/login")
            self.ClearCookie()
            self.end_headers()
            return

        """ BOXES
            ------------------
        """    
        if self.path=='/boxes':
            self.wbody("/boxes.html")
            return

        if parsed_path.path=='/boxes/get':
            bl=self.db.sets['box_lastid']
            lastid=self._getval('lastid',None)
            if lastid and lastid==bl:
                j=json.dumps({'lastid':bl})
                self.wjson(j)
                return
            br=int(self.db.sets['box_row'])
            bc=int(self.db.sets['box_col'])
            box_count=int(self.db.sets['box_count'])
            boxes=self.db._gets(TB_BOXES_HD)
            j=json.dumps({'box_count':box_count,'box_row':br,'box_col':bc,'boxes':boxes,'lastid':bl},ensure_ascii=False)
            self.wjson(j)
            return

        """ ZAKAZ
            ------------------
        """    

        if parsed_path.path=='/zakaz/block':
            id=self._getval('id',0)
            unblock=self._getval('unblock',None)
            if  id==0:
                self.return_false()
                return
            if unblock!=None:
                stat=2
            else:
                stat=3
            try:
                ice_lock()
                box=self.db._getid(TB_BOXES_HD,int(id))
                allow=True
                if unblock==None and (box['status']<1 or box['status']>2 or box['d_counts']==0):
                    allow=False
                if allow:
                    self.db.boxes_update_time(id,{'status':stat})
                    box_sub=self.db.boxes_get_sublink(id)
                    for b in box_sub:
                        self.db.boxes_update_time(b['id'],{"status":stat})
            finally:
                ice_unlock()
            if not allow:
                self.return_false()
                return
            j=json.dumps({'result':True,'id':id})
            self.wjson(j)
            return

        if parsed_path.path=='/zakaz/clear':
            id=self._getval('id',None)
            if not id:
                self.return_false()
                return
            try:
                ice_lock()
                box=self.db._getid(TB_BOXES_HD,int(id))
                allow=True
                if allow:
                    self.db._delete(TB_BOXES_CT,"idhd=%s" % id)
                    self.db.boxes_update_time(id,{'status':0,'idhd':0})
                    box_sub=self.db.boxes_get_sublink(id)
                    for b in box_sub:
                        self.db._delete(TB_BOXES_CT,"idhd=%s" % b['id'])
                        self.db.boxes_update_time(b['id'],{"status":0,'idhd':0})
            finally:
                ice_unlock()
            if not allow:
                self.return_false()
                return
            j=json.dumps({'result':True,'id':id})
            self.wjson(j)
            return

        """ BOX
            ------------------
        """    
        if parsed_path.path=='/box/open':
            id=self._getval('id',None)
            if not id:
                self.return_false()
                return

            try:
                ice_lock()
                box=self.db._getid(TB_BOXES_HD,int(id))
                if box['status']==0:
                    self.db.boxes_update_time(id,{'status':1})
            finally:
                ice_unlock()

            if box['status']==3:
                self.return_false()
                return
            j=json.dumps({'result':True,'id':id})
            self.wjson(j)
            return

        if parsed_path.path=='/box':
            id=self._getval('id','1')
            html=self.get_file('/box.html')
            html = ht_reptags_arr(html,["%id%"],[id])
            self.wbodyh(html)
            return

        if parsed_path.path=='/box/get':
            id=self._getval('id',None)
            lastid=self._getval('lastid',None)
            if not id:
                self.return_false()
                return
            (hd,ct)=self.db._get_data_hd_ct(TB_BOXES_HD,TB_BOXES_CT,int(id))
            blast=str(hd['dt']).replace('.','_')+"_"+str(hd['tm']).replace(':','_')
            if lastid==blast:
                j=json.dumps({'result':False})
                self.wjson(j)
                return
            j=json.dumps({'result':True,'box_hd':hd,'box_ct':ct,'lastid':blast})
            self.wjson(j)
            return

        if parsed_path.path=='/box/del':
            id=self._getval('id',None)
            if not id:
                self.return_false()
                return

            result=False
            try:
                ice_lock()
                box=self.db._getid(TB_BOXES_HD,int(id))
                if box['status']<2:
                    """ Если есть подчиненные, то перепривязываем из на первого """
                    dt=my.curdate2my()
                    tm=my.curtime2my()
                    if box['d_sub']>0:
                        box_sub=self.db.boxes_get_sublink(id)
                        firstid=box_sub[0]['id']
                        for b in box_sub:
                            if b['id']!=firstid:
                                hid=firstid
                            else:
                                hid=0
                            self.db.boxes_update_time(b['id'],{"idhd":hid})

                    self.db._delete(TB_BOXES_CT,"idhd=%s" % id)
                    self.db.boxes_update_time(id,{'status':0,"idhd":0})
                    result=True
            finally:
                ice_unlock()

            j=json.dumps({'result':result})
            self.wjson(j)
            return

        if parsed_path.path=='/box/link':
            id=self._getval('id',None)
            to=self._getval('to',None)
            if not id or not to:
                self.return_false()
                return
            id=int(id)
            to=int(to)
            result=False
            try:
                ice_lock()
                box =self.db._getid(TB_BOXES_HD,id)
                box2=self.db._getid(TB_BOXES_HD,to)

                if box['status']>0 and box['status']<3:
                    allow=True
                else:
                    allow=False
                """ Если на текущую корзину были ссылки """
                if allow and box['d_sub']>0:    
                    relink=True
                    relink_idhd=box['idhd']
                else:
                    relink=False
                """ Корзина к которой привязываем может быть уже связана """
                if allow and box2['idhd']!=0:
                    to=box2['idhd']
                    box2=self.db._getid(TB_BOXES_HD,box2['idhd'])
                    """ Если связь нарушена или циклическая """
                    if box2==None or id==to:
                        allow=False
                """ Если главная корзина недоступна """
                if allow and not(box2['status']>0 and box['status']<3):
                    allow=False
                """ Привязываем """
                if allow:
                    self.db.boxes_update_time(id,{"idhd":to})
                """ Привязываем подчиненные """
                if allow and relink:
                    box_sub=self.db.boxes_get_sublink(id)
                    for b in box_sub:
                        self.db.boxes_update_time(b['id'],{"idhd":to})

            finally:
                ice_unlock()

            j=json.dumps({_RESULT:allow})
            self.wjson(j)
            return

        if parsed_path.path=='/box/unlink':
            id=self._getval('id',None)
            if not id:
                self.return_false()
                return
            id=int(id)

            result=False
            try:
                ice_lock()
                box=self.db._getid(TB_BOXES_HD,int(id))
                if box['status']<3:
                    self.db.boxes_update_time(id,{"idhd":0})
                    result=True
            finally:
                ice_unlock()

            j=json.dumps({_RESULT:result})
            self.wjson(j)
            return

        if parsed_path.path=='/box/setstatus':
            id=self._getval('id',None)
            if not id:
                self.return_false()
                return
            id=int(id)
            result=False
            try:
                ice_lock()
                box=self.db._getid(TB_BOXES_HD,id)
                st=0
                if box['status']==1 and box['d_counts']>0:
                    st=2
                if box['status']==2:
                    st=1
                if st>0:
                    self.db.boxes_update_time(id,{"status":st})
                    result=True
            finally:
                ice_unlock()

            j=json.dumps({_RESULT:result})
            self.wjson(j)
            return

        if parsed_path.path=='/box/ct/add':
            id   = self._getval('id',None)
            code = self._getval('code',None)
            barcode = self._getval('barcode',None)
            count = self._getval('count',1)
            if not id or (not code and not barcode):
                self.return_false()
                return
            id=int(id)
            result=False
            try:
                ice_lock()
                box=self.db._getid(TB_BOXES_HD,id)
                if box['status']>0 and box['status']<3:
                    allow=True
                else:
                    allow=False

                if barcode and not _verify_EAN(barcode):
                    allow=False

                if barcode and _verify_EAN(barcode):
                    if isprefix(self.db.sets['scale_prefix'],barcode):
                        code=barcode[2:7].lstrip("0")
                        count=barcode[7:12]
                        count=count[0:2]+"."+count[2:]
                    else:
                        r=self.db._search_shk(barcode)
                        if r:
                            code=self.db.price['id']
                        else:
                            allow=False
                    
                if allow:
                    self.db._insert(TB_BOXES_CT,{'idhd':id,'code':code,'count':count})
                    self.db.boxes_update_time(id)
                    result=True
            finally:
                ice_unlock()

            j=json.dumps({_RESULT:result})
            self.wjson(j)
            return

        if parsed_path.path=='/box/ct/upd':
            idhd   = self._getval('idhd',None)
            id     = self._getval('id',None)
            storno = self._getval('storno',None)
            count  = self._getval('count',None)
            struct={}
            if count:
                count=float(count)
                if count<0:
                    self.return_false()
                    return
                if count==0:
                    count=None
                    storno=1
                else:
                    struct['count']=count
            if storno:
                struct['storno']=storno
            if not id or not idhd:
                self.return_false()
                return
            idhd=int(idhd)
            id=int(id)
            result=False
            try:
                ice_lock()
                ct=self.db._select( TB_BOXES_CT, "idhd=%s and id=%s" % (idhd,id) )
                price=self.db._getid(TB_PRICE,ct[0]['code'])
                box=self.db._getid(TB_BOXES_HD,idhd)
                if box['status']>0 and box['status']<3:
                    allow=True
                else:
                    allow=False
                if price['real']==0 and type(count)==float and math.modf(count)[0]!=0:
                    allow=False
                if allow:
                    self.db._update(TB_BOXES_CT,struct,"idhd=%s and id=%s" % (idhd,id))
                    self.db.boxes_update_time(idhd)
                    result=True
            finally:
                ice_unlock()

            j=json.dumps({_RESULT:result})
            self.wjson(j)
            return

        """ PRICE
            ------------------
        """    
        if parsed_path.path=="/price/get":
            openid = self._getval('openid','0')
            isup   = self._getval('isup','0')
            if isup!='0':
                price  = self.db._getid(TB_PRICE,openid)
                if price==None:
                    openid=0
                else:
                    openid=price['idgroup']
            price  = self.db._gethd(TB_PRICE,openid)
            j=json.dumps({_RESULT:True,'pricelist':price,'openid':openid})
            self.wjson(j)
            return

        """ PRINT
            ------------------
        """    
        if parsed_path.path=="/print/numbox":
            id  = self._getval('id',None)
            if not id:
                self.return_false()
                return
            id=int(id)
            box=self.db._getid(TB_BOXES_HD,id)
            if box['idhd']!=0:
                id=box['idhd']
            printer=self.db.user['printer']
            self.create_dtp()
            img  = Image.new("1", (250, 250))
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 200)
            draw.text((10, 10),str(id).rjust(2,"0"),1,font=font)
            img.save('../dIceCash/DTPrint/site/files/num.jpg')
            self.dtpclient._cm(printer,"prn_lines",{'text':u"ЗАКАЗ","width":0,"height":1,"font":1,"bright":10,"big":1,"invert":0,"align":"center"})
            self.dtpclient._cm(printer,"prn_lines",{'text':my.mydt2normdt(box['dt']),"width":0,"height":1,"font":1,"bright":10,"big":1,"invert":0,"align":"left"})
            self.dtpclient._cm(printer,"prn_lines",{'text':box['tm'],"width":0,"height":1,"font":1,"bright":10,"big":1,"invert":0,"align":"left"})
            self.dtpclient._cm(printer,"print_text",{'text':""})
            self.dtpclient._cm(printer,"set_style",{'adata':['','','','center','']})
            self.dtpclient._cm(printer,"print_image",{'filename':"num.jpg"})
            #self.dtpclient._cm(printer,"print_text",{'text':""})
            #self.dtpclient._cm(printer,"roll",{'count':8})
            self.dtpclient._cm(printer,"cut",{'type':1})
            del self.dtpclient
            j=json.dumps({_RESULT:True})
            self.wjson(j)
            return

        self._send_HEAD("text/html",404)

    def do_POST(self):
        self.cur_css='blue.css'
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        
        if not self.mysql_open():
            self._send_HEAD("text/html",404)
            print "error. not open mysql"
            return
        else:
            self.db.sets_read()()

        if self.path=='/sets/autosets':
            if form.has_key("save"):
                if self.currule<RULE_ADMIN:
                    self._redirect("/")
                    return
                qs=self.db.tb_sets._upd_post(form,'device')
                for q in qs:
                    self.db.run(q)
            self._redirect("/sets")
            return

        self._send_HEAD("text/html",404)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ Создаем веб сервер многопоточный """

if __name__ == '__main__':
    db = dbIceRest(DATABASE, MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD) 
    if db.open():
        pass
    else:
        print "Database not exist"
        sys.exit(1)

    db.sets_read()
    #db._create()
    print "opened database"

    server = ThreadedHTTPServer(('', int(db.sets['server_port'])+2), Handler)
    print 'Start dIceRest Server v %s [%s]' % (VERSION,int(db.sets['server_port'])+2)
    db.close()
    server.serve_forever()

