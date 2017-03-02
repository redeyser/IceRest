function _putfile(page) {
    var file = document.getElementById("file");
    file=file.files[0]
    if (!file) { return; }
    var xhr = new XMLHttpRequest();
    xhr.open("POST", page, false);
    var formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
    return xhr.responseText;
}

function _getdata(page){
    var xhrp = new XMLHttpRequest();
    xhrp.open('GET', page, false);
    xhrp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhrp.send();
        if (xhrp.status != 200) {
            alert( xhrp.status + ': ' + xhrp.statusText );
            return '#err';
        } else {
            return xhrp.responseText;
        }
        return '#err';
}

function async_get(page,funct){
    var xhrp = new XMLHttpRequest();
    xhrp.open('GET', page, true);
    xhrp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhrp.send();

    xhrp.onreadystatechange = function() { 
        if (xhrp.readyState != 4) return;
        // RECIEVED ...
        if (xhrp.status != 200) {
            // ERROR
        } else {
            // OK
            funct(xhrp.responseText);
        }
    }   
    // BEGIN
    // ...
}

function _postdata(page,a_params,a_values){
    var xhrp = new XMLHttpRequest();
    xhrp.open('POST', page, false);
    xhrp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    body="";
    for(var i=0; i<a_params.length; i++) {
        n=a_params[i];
        v=a_values[i];
        if (body.length>0){add="&";}else{add="";}
        body = body + add + n + "=" + encodeURIComponent(v);
    }
    xhrp.send(body);
        if (xhrp.status != 200) {
            alert( xhrp.status + ': ' + xhrp.statusText );
            return '#err';
        } else {
            return xhrp.responseText;
        }
        return '#err';
}

function _relocate(page){
    window.location=page;
}

function showdoc(d){
    content=_getdata("/help?id="+d);
    doctext.innerHTML=content;
    doc.hidden=false;
}
function alert_message(head,content){
  message_content.innerHTML="<div class='infoline center'>"+head+"</div>"+content;
  message.hidden=false;
//  message_btn.focus();
}
function loadboxes(){
    LASTID="";
    result=_getdata("/boxes/get");
    json=JSON.parse(result);
    LID=json['lastid'];
    if (LID!=LASTID){
        LASTID=LID;
    }
    cols=parseInt(json['box_col']);
    rows=parseInt(json['box_row']);
    boxes=json['boxes'];
    r=1;c=1;
    ct="";
    for (k in boxes){
        b=boxes[k];
        id=b['id'];
        if (c==1){
            ct+="<tr>";
        }
        on="q_boxclick(this);";
        bid='box_'+id;
        td="<td class='rtext padd' id='"+bid+"' onclick=\""+on+"\">"+
            "</td>";
        ct+=td;
        c+=1;
        if (c>cols){
            c=1;r+=1;
            ct+="</tr>";
        }
    }
    box=document.getElementById("boxes");
    box.innerHTML=ct;

    for (k in boxes){
        putbox(boxes[k]);
    }
}

function putbox(b){
    id=b['id'];
    counts=parseInt(b['d_counts']);
    idhd=parseInt(b['idhd']);
    d_sub=parseInt(b['d_sub']);
    status=parseInt(b['status']);
    on="q_boxclick(this);";
    bid='box_'+id;
    
    box=document.getElementById(bid);

    if (status==0){
        src="/images/b0.png";
        bg='bg0';
    }
    if (status==1){
        if (counts>0){
            src="/images/b11.png";
        }else{
            src="/images/b1.png";
        }
        bg='bg0';
    }
    if (status==2){
        src="/images/b2.png";
        bg='bg0';
    }
    if (status==3){
        src="/images/b3.png";
        bg='bg0';
    }
    if (idhd!=0){
        sidhd=idhd; if (idhd<10){  sidhd='0'+idhd; }
        opn="<span class='small black posa bg bgh hid' >"+sidhd+"</span>";
    }else{
        opn="";
    }
    if (d_sub!=0){
        bg='bgh';
    }
    sid=id; if (id<10){  sid='0'+id; }
    if (counts==0){
        counts="";
    }
    box.innerHTML=
        "<div class='wall ltext' style='height:95%;padding-top:5px;float:left;'>"+  
        "<span class='small black bg "+bg+"' style='float:bottom'>"+sid+"</span>"+opn+
        "<img class='box' src='"+src+"'/>"+
        "<span class='norm black posa'>"+counts+"</span"+
        "</div>";
    boxes[id-1]=b;
}
function refboxes(){
    async_get("/boxes/get?lastid="+LASTID,_refboxes);
}
function _refboxes(j){
    json=JSON.parse(j);
    LID=json['lastid'];
    if (LID==LASTID){
        return;
    }
    LASTID=LID;
    lastid=document.getElementById("lastid");
    if (lastid){ lastid.innerHTML=LASTID; }
    boxes_new=json['boxes'];
    if (boxes_new.length==0){
        return;
    }
    for (k in boxes){
        t=false;
        if (boxes[k]['d_counts']!=boxes_new[k]['d_counts']){
         t=true;   
        }
        if (boxes[k]['idhd']!=boxes_new[k]['idhd']){
         t=true;   
        }
        if (boxes[k]['status']!=boxes_new[k]['status']){
         t=true;   
        }
        if (t){
            putbox(boxes_new[k]);
        }
    }
}
function loadprice(isup){
    async_get("/price/get?openid="+PRICE_CURRENT+'&isup='+isup,_loadprice);
}
function _loadprice(j){
    json=JSON.parse(j);
    //alert(j);
    pricelist=json['pricelist'];
    PRICE_CURRENT=json['openid'];
    PRICE_TOP=0;
    _showprice(PRICE_TOP);
}
function _showprice(pt){
    PL=pricelist.length-1;
    if (pt>PL){
        return;
    }
    PRICE_TOP=pt;
    cols=5; rows=4;
    pb=pt+cols*rows-1;
    if (pb>PL){
        pb=PL;
    }
    r=1;c=1;
    ct="";
    for (r=1;r<=rows;r++){
        ct+="<tr>";
        for (c=1;c<=cols;c++){
         i=pt+(r-1)*cols+(c-1);
         if (i<=pb){
            p=pricelist[i];
            id=p['id'];
            on="priceclick("+i+");";
            bid='price_'+id;
            name=p['name'];
            if (p['istov']=='0'){
                cl='bgdir';
            }else{
                cl='bgtov';
            }
         }else{
            cl='';
            on="";
            bid='price_null';
            name='';
         }
            td="<td class='w10 h20 pwrap vcenter center ohid "+cl+"' id='"+bid+"' onclick=\""+on+"\">"+name+
                "</td>";
            ct+=td;
        }
        ct+="</tr>";
    }
    if (pt==0){ imgup.hidden=true;  }else{  imgup.hidden=false;  }
    if (pt+20>PL){ imgdown.hidden=true;  }  else { imgdown.hidden=false;  }
    prices=document.getElementById("prices");
    prices.innerHTML=ct;
}
function clickdown(){
    PL=pricelist.length-1;
    pt=PRICE_TOP+20;
    if (pt>PL){
        pt=pt-20;
    }
    _showprice(pt);

}
function clickup(){
    PL=pricelist.length-1;
    pt=PRICE_TOP-20;
    if (pt<0){
        pt=pt+20;
    }
    _showprice(pt);

}
function warn_alert(t,f){
    warning.hidden=false;
    warn_content.innerHTML=t;
    answer=f;
    lbno.hidden=false;
}
function info_alert(t){
    warning.hidden=false;
    warn_content.innerHTML=t;
    lbno.hidden=true;
    answer=null;
}

