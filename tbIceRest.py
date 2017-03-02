#!/usr/bin/python
# -*- coding: utf-8
"""
    Tables of IceRest
"""
import my

class tb_users(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('login','s')
        self.addfield('password','s')
        self.addfield('type','d')
        self.addfield('code','s')
        self.addfield('idtab','d')
        self.addfield('css','s')
        self.addfield('cur_price','s')
        self.addfield('printer','s')
        self.record_add = self.fieldsorder[1:4]

    def _getid(self,login="",id=0):
        if login=="":
            _if="id=%d" % id
        else:
            _if="login='%s'" % login
        return self.query_all_select()+" where %s" % _if

    def _gets(self):
        return self.query_all_select() + " where type=10 order by login"

class tb_sets(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('group','s')
        self.addfield('name','s')
        self.addfield('value','s')

    def _getid(self,name):
        return self.query_select(['value']," where name='%s'" % name)

    def _gethd(self,name):
        return self.query_select(['value']," where group='%s'" % name)

class tb_price(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','s')
        self.addfield('shk','s')
        self.addfield('name','s')
        self.addfield('litrag','f')

        self.addfield('cena','f')
        self.addfield('ostatok','f')
        self.addfield('sheme','d')
        self.addfield('real','d')

        self.addfield('section','d')
        self.addfield('max_skid','f')
        self.addfield('type','d')
        self.addfield('alco','d')

        self.addfield('minprice','f')
        self.addfield('maxprice','f')
        self.addfield('reserved2','s')
        self.addfield('idgroup','s')
        self.addfield('istov','d')

    def _gethd(self,parent):
        return self.query_all_select()+" where idgroup='%s' order by istov,name" % parent

    def _getid(self,code):
        if code!=None:
            _if=" where id='%s'" % code
        else:
            _if=""
        return self.query_all_select()+_if

    def _find_shk(self,shk):
        return self.query_all_select()+"where shk='%s'" % (shk)

class tb_price_shk(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('shk','s')
        self.addfield('name','s')
        self.addfield('cena','f')
        self.addfield('koef','f')

    def _getidhd(self,code,shk=None):
        if shk!=None:
            _if=" and shk='%s'" % shk
        else:
            _if=""
        return self.query_all_select()+"where id='%s' %s group by cena order by cena desc" % (code,_if)

    def _find_shk(self,shk):
        return self.query_all_select()+"where shk='%s'" % (shk)

class tb_boxes_hd(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('idhd','d')
        self.addfield('status','d')
        self.addfield('counts','d')
        self.addfield('opened','d')
        self.addfield('iduser','d')
        self.addfield('dt','D')
        self.addfield('tm','t')

    def _create(self):
        q="""create table `%s` (
        `id`      smallint(2) unsigned NOT NULL,
        `idhd`    smallint(2) default 0,
        `status`  tinyint(1)  default 0,
        `counts`  tinyint(1)  default 0,
        `opened`  tinyint(1)  default 0,
        `iduser`  tinyint(1)  default 0,
        `dt`      date,
        `tm`      time,
        primary key (`id`),
        key `status` (`status`) ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _gets(self):
        self.query_all_select()
        self.query_fields.append("d_sub")
        self.query_fields.append("d_counts")
        return "select *,(select count(*) from %s as b where b.idhd=a.id) as d_sub,\
        (select count(*) from tb_boxes_ct as b where b.idhd=a.id and b.storno=0) as d_counts\
        from %s as a" % (self.tablename,self.tablename)
        #return self.query_all_select()

    def _getid(self,id):
        self.query_all_select()
        self.query_fields.append("d_sub")
        self.query_fields.append("d_counts")
        return "select *,(select count(*) from %s as b where b.idhd=a.id) as d_sub,\
        (select count(*) from tb_boxes_ct as b where b.idhd=a.id and b.storno=0) as d_counts\
        from %s as a where id=%s" % (self.tablename,self.tablename,id)

class tb_boxes_ct(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('idhd','d')
        self.addfield('id','d')
        self.addfield('code','d')
        self.addfield('count','f')
        self.addfield('storno','d')

    def _create(self):
        q="""create table `%s` (
        `idhd`    smallint(2) default 0,
        `id`      int(4) AUTO_INCREMENT,
        `code`    int(4),
        `count`   decimal(8,3)  default 1,
        `storno`  tinyint(1) default 0,
        primary key (`idhd`,`id`) ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _gethd(self,idhd):
        self.query_all_select()
        self.query_fields.append("d_price")
        self.query_fields.append("d_cena")
        return "select ct.*,(select name from tb_price as p where p.id=ct.code) as d_price,\
        (select cena from tb_price as p where p.id=ct.code) as d_cena\
        from %s as ct where idhd=%s" % (self.tablename,idhd)

