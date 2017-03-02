#!/usr/bin/python
# -*- coding: utf-8
# DataBase for IceRest
import my
import os
import re
import tbIceRest as tbs
from datetime import datetime
from md5 import md5

DATABASE = "IceCash"
MYSQL_USER = "icecash"
MYSQL_PASSWORD = "icecash1024"

TB_USERS     = "tb_users"
TB_SETS      = "tb_sets"
TB_PRICE     = "tb_price"
TB_PRICE_SHK = "tb_price_shk"
TB_BOXES_HD  = "tb_boxes_hd"
TB_BOXES_CT  = "tb_boxes_ct"

def cur_dttm():
    return datetime.now().strftime(format="%Y_%m_%d_%H_%M_%S")

def _round(V,n):
    z=str(V.__format__(".4f")).split(".")
    if len(z)<2:
        return str(V)
    else:
        d=int(z[0])
        f=z[1].ljust(n,"0")
    l=len(f)
    a=[]
    for i in range(l):
        a.append(int(f[i]))
    r=range(l)[n:]
    r.reverse()
    x=range(l)[:n]
    x.reverse()
    ost=0
    for i in r:
        a[i]+=ost
        if a[i]>=5:
            ost=1
        else:
            ost=0
    for i in x:
        a[i]+=ost
        if a[i]>9:
            a[i]=0
            ost=1
        else:
            ost=0
            break
    d+=ost
    s=""
    for i in range(n):
        s+=str(a[i])
    if n>0:
        s="."+s
    result=str(d)+s
    return result

class dbIceRest(my.db):

    def _tbinit(self,name):
        tb=getattr(tbs, name)
        self.tbs[name] = tb(name)

    def _tbcreate(self,tn):
        self.run(self.tbs[tn]._create())

    def _recreate(self):
        for name in self.tbs.keys():
            if not name in self.tables:
               self._tbcreate(name)
               print "created table %s" % name

    def _tables(self):
        res=self.get("show tables")
        db=[]
        for r in res:
            db.append(r[0])
        self.tables=db

    """ Переопределенный расширенный метод. Подключение, проверка таблиц, создание не существующих """
    def open(self,recreated=True):
        r=my.db.open(self)
        if r:
            self._tables()
            if recreated:
                self._recreate()
        return r

    def __init__(self,dbname,host,user,password):
        my.db.__init__(self,dbname,host,user,password)
        self.tbs={}
        self._tbinit(TB_USERS)
        self._tbinit(TB_SETS)
        self._tbinit(TB_PRICE)
        self._tbinit(TB_PRICE_SHK)
        self._tbinit(TB_BOXES_HD)
        self._tbinit(TB_BOXES_CT)

    def _create(self):
        self._truncate(TB_BOXES_HD)
        self._truncate(TB_BOXES_CT)
        self.sets_read()
        self.sets_insert('rest_boxes','box_count','30')
        self.sets_insert('rest_boxes','box_row','5')
        self.sets_insert('rest_boxes','box_col','6')
        self.sets_insert('rest_boxes','box_lastid','0')
        for i in xrange(30):
            self._insert(TB_BOXES_HD,{'id':i+1})

    """ Optimize functions ----------------------- """

    def _gets(self,tn,tostr=False,dttm2str=True):
        result = self.get(self.tbs[tn]._gets())
        if len(result)==0:
            return None
        else:
            res=[]
            for r in result:
                res.append(self.tbs[tn].result2values(r,tostr=tostr,dttm2str=dttm2str))
            return res

    """ Получить запись по id """
    def _getid(self,tn,id,tostr=False,dttm2str=True):
        res = self.get(self.tbs[tn]._getid(id))
        if len(res)==0:
            return None
        else:
            return self.tbs[tn].result2values(res[0],tostr=tostr,dttm2str=dttm2str)

    """ Получить записи по idhd """
    def _gethd(self,tn,id,tostr=False,dttm2str=True):
        res = self.get(self.tbs[tn]._gethd(id))
        if len(res)==0:
            return []
        else:
            result=[]
            for r in res:
                result.append( self.tbs[tn].result2values(r,tostr=tostr,dttm2str=dttm2str) )
        return result

    """ Получить Заголовочную запись и подчиненные """
    def _get_data_hd_ct(self,tb_hd,tb_ct,id,tostr=False,dttm2str=True):
        hd = self._getid(tb_hd,id,tostr=tostr,dttm2str=dttm2str)
        if hd != None:
            ct = self._gethd( tb_ct,id,tostr=tostr,dttm2str=dttm2str ) 
        else:
            ct=None
        return (hd,ct)

    """ Очистить таблицу """    
    def _truncate(self,tn):
        self.run("truncate %s" % tn)
        return True

    """ Переделать в хэш """
    def _db2hash(self,r,id,val):
        h={}
        for rec in r:
            h[rec[id]]=rec[val]
        return h

    """ Переделать в массив """
    def _db2arr(self,r,id):
        t=[]
        for rec in r:
            t.append(rec[id])
        return t

    """ Простая выборка """
    def _select(self,tn,where="",fields=None,order=None,group=None,tostr=False,dttm2str=True,toarr=False,tohash=False,nofields=False):
        self.result_order=[]
        if where!="" and fields==None:
            where= " where %s" % where
        if group:
            _group=" group by "+group
        else:
            _group=""
        if order:
            _order=" order by "+order
        else:
            _order=""
        if fields==None:
            result = self.get(self.tbs[tn].query_all_select()+where+_group+_order)
        else:
            result = self.get(self.tbs[tn].query_select(fields,where)+_group+_order)
        if len(result)==0:
            return []
        else:
            if toarr:
                res=[]
                for r in result:
                    if tostr:
                        s=str(r[0])
                    else:
                        s=r[0]
                    res.append(s)
                return res
            if tohash:
                res={}
                self.result_order=[]
                for r in result:
                    if tostr:
                        s=str(r[1])
                    else:
                        s=r[1]
                    res[r[0]]=s
                    self.result_order.append(r[0])
                return res
            res=[]
            if not nofields:
                for r in result:
                    res.append(self.tbs[tn].result2values(r,tostr=tostr,dttm2str=dttm2str))
            else:
                res=result
            return res

    """ Добавить запись """
    def _insert(self,tn,struct):
        r=self.run(self.tbs[tn].query_insert(struct))
        if not r:
            self.lastid=0
            return False
        self.lastid=self.get(my.Q_LASTID)[0][0]
        return True

    """ Изменить запись """
    def _update(self,tn,struct,where):
        return self.run(self.tbs[tn].query_update(struct)+" where %s" % where)

    """ Удалить запись """
    def _delete(self,tn,where):
        return self.run(self.tbs[tn].query_delete(where))

    """ Пустая запись """
    def _empty(self,tn):
        return self.tbs[tn].empty_all_values()

    """ ------------------------------------------ """

    def sets_read(self):
        self.sets = self._select(TB_SETS,"",['name','value'],tohash=True)

    def sets_insert(self,g,n,v):
        r=self._getid(TB_SETS,n)
        if r:
            return False
        else:
            self._insert(TB_SETS,{'group':g,'name':n,'value':v})
            return True

    def sets_update_box_lastid(self):
        tm=cur_dttm()
        self._update(TB_SETS,{'value':tm},"name='box_lastid'")

    def boxes_get_sublink(self,id):
        return self._select(TB_BOXES_HD," idhd=%s" % id)

    def boxes_update_time(self,id,st={}):
        dt=my.curdate2my()
        tm=my.curtime2my()
        struct={"dt":dt,"tm":tm}
        struct.update(st)
        self._update(TB_BOXES_HD,struct,"id=%s" % id)
        return self.sets_update_box_lastid()

    def _user_auth(self,login,password):
        self.user=self._getid(TB_USERS,login)
        if self.user==None:
            return False
        else:
            if md5(password).hexdigest()==self.user['password']:
                return True
            else:
                return False

    def _search_shk(self,shk):
        self.price = self._select(TB_PRICE,"shk='%s'" % (shk))
        if len(self.price)==0:
            priceshk = self._select(TB_PRICE_SHK,"shk='%s'" % (shk))
            if len(priceshk)==0:
                self.price=None
                self.price_shk=None
                return False
            self.price=self._getid(TB_PRICE,int(priceshk[0]['id']))
            if not self.price:
                self.price=None
                self.price_shk=None
                return False
            self.price['name']=priceshk[0]['name']
            if priceshk[0]['koef']!=0:
                self.price['cena']=priceshk[0]['koef']*self.price['cena']
            else:
                self.price['cena']=priceshk[0]['cena']
            return True
        else:
            self.price=self.price[0]
        return True

