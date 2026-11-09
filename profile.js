/* Private master-CV editor for authenticated users.
   Never includes the private staging CV or a privileged backend key in public code. */
(() => {
  const BASE='https://lpbqzagdforlafvavgkx.supabase.co';
  const PUB='sb_publishable_OLazvsr0InC3O_6Ox292LA_GDmsnZs6';
  const $=id=>document.getElementById(id);
  let savedText='',currentProfile=null;
  const status=text=>{if($('cvMessage'))$('cvMessage').textContent=text;};
  const api=async(path,token,options={})=>{
    const r=await fetch(BASE+path,{...options,headers:{apikey:PUB,Authorization:'Bearer '+token,...(options.headers||{})}});
    if(!r.ok) {
      const data=await r.json().catch(()=>({}));
      throw Error(data.message||data.error||'Error HTTP '+r.status);
    }
    return r.status===204?null:r.json().catch(()=>null);
  };
  async function load(){
    if(!window.trabajoAuth?.isLoggedIn()){status('Inicia sesión para consultar o guardar tu CV privado.');$('cvMaster').value='';$('cvMaster').disabled=true;$('cvSave').disabled=true;$('cvDownload').disabled=true;return;}
    $('cvMaster').disabled=false;$('cvSave').disabled=false;$('cvDownload').disabled=false;
    status('Cargando CV...');
    try {
      const result=await window.trabajoAuth.withSession((token,uid)=>api('/rest/v1/candidate_profiles?select=master_cv_text,updated_at&user_id=eq.'+encodeURIComponent(uid),token));
      currentProfile=result?.[0]||null;
      savedText=currentProfile?.master_cv_text||'';
      $('cvMaster').value=savedText;
      status(savedText?'CV privado cargado desde Supabase.':'Todavía no existe un CV asociado a tu usuario. El CV original está en importación privada, pendiente de vincular.');
    }catch(err){status('No se pudo cargar tu CV: '+err.message);}
  }
  async function save(){
    if(!window.trabajoAuth?.isLoggedIn()){status('Inicia sesión primero.');return;}
    const text=$('cvMaster').value.trim();
    if(!text){status('No se puede guardar un CV vacío.');return;}
    $('cvSave').disabled=true;status('Guardando...');
    try {
      await window.trabajoAuth.withSession((token,uid)=>api('/rest/v1/candidate_profiles?on_conflict=user_id',token,{
        method:'POST',
        headers:{'Content-Type':'application/json',Prefer:'resolution=merge-duplicates,return=minimal'},
        body:JSON.stringify({user_id:uid,master_cv_text:text,updated_at:new Date().toISOString()})
      }));
      savedText=text;status('CV guardado en tu cuenta privada de Supabase.');
    }catch(err){status('No se pudo guardar: '+err.message);}
    finally{$('cvSave').disabled=false;}
  }
  function download(){
    if(!window.trabajoAuth?.isLoggedIn())return;
    const text=$('cvMaster').value||'';
    const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download='trabajoai-cv-maestro.txt';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),500);
  }
  document.addEventListener('DOMContentLoaded',()=>{
    $('cvSave')?.addEventListener('click',save);
    $('cvDownload')?.addEventListener('click',download);
    $('cvRefresh')?.addEventListener('click',load);
    document.addEventListener('trabajo-auth-change',load);
    load();
  });
})();