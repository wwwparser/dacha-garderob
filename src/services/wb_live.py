"""Read live WB stock in the user's existing browser session. Never sends cart actions."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/skills/browser-bridge'))
import bridge
bridge.set_session('dacha-stock')

def evaluate(code):
    result=bridge.js_eval(code)
    if isinstance(result,dict) and result.get('_error'):
        raise RuntimeError(result['_error'])
    return result

CAPTURE = r'''(()=>{
  if(window.__dachaCaptureInstalled)return;
  window.__dachaCaptureInstalled=true;
  window.__dachaResponses=[];
  const eligible=u=>/\/__internal\/(card\/cards|search)/.test(u);
  const save=(url,status,body)=>{try{if(status===200)window.__dachaResponses.push({url,status,data:JSON.parse(body)})}catch(e){}};
  const oldFetch=window.fetch;
  window.fetch=async function(...args){const r=await oldFetch.apply(this,args);const u=typeof args[0]==='string'?args[0]:args[0]?.url||String(args[0]);if(eligible(u))r.clone().text().then(t=>save(u,r.status,t));return r};
  const open=XMLHttpRequest.prototype.open,send=XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open=function(method,url,...args){this.__dachaUrl=String(url);return open.call(this,method,url,...args)};
  XMLHttpRequest.prototype.send=function(...args){if(eligible(this.__dachaUrl||''))this.addEventListener('load',()=>{try{save(this.__dachaUrl,this.status,this.responseText)}catch(e){}});return send.apply(this,args)};
})()'''

def install_capture():
    bridge.cdp('Page.addScriptToEvaluateOnNewDocument',{'source':CAPTURE})

def navigate(url):
    bridge.cdp('Page.navigate',{'url':url})

def responses():
    return evaluate('''(window.__dachaResponses||[]).map(r=>({url:r.url,status:r.status,data:{products:(r.data.products||[]).map(p=>({id:p.id,name:p.name,brand:p.brand,root:p.root,totalQuantity:p.totalQuantity,feedbacks:p.feedbacks,reviewRating:p.reviewRating,kindId:p.kindId,subjectId:p.subjectId,supplier:p.supplier,sizes:(p.sizes||[]).map(s=>({name:s.name,origName:s.origName,wh:s.wh,price:s.price,stocks:s.stocks,optionId:s.optionId}))}))}}))''')
