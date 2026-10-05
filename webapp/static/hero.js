import * as THREE from './three.module.min.js';
const canvas=document.querySelector('#radar-art'),host=canvas.parentElement;
if(!matchMedia('(max-width:700px)').matches)try{
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(35,1,.1,100);camera.position.set(0,0,11);
const sculpture=new THREE.Group();scene.add(sculpture);
const colors=[0x114e46,0xfa836d,0x18271f,0xf5f0d4];
// Abstract geometry, never measured audit data.
for(let i=0;i<4;i++){const material=new THREE.MeshStandardMaterial({color:colors[i],roughness:.45,metalness:.12});const ring=new THREE.Mesh(new THREE.TorusGeometry(2.2-i*.25,.09+i*.025,8,70),material);ring.rotation.set(i*.65,.45+i*.6,i*.8);sculpture.add(ring);}
const core=new THREE.Mesh(new THREE.IcosahedronGeometry(1.12,0),new THREE.MeshStandardMaterial({color:0xfa836d,roughness:.7,flatShading:true}));sculpture.add(core);
const frame=new THREE.Mesh(new THREE.IcosahedronGeometry(1.38,0),new THREE.MeshBasicMaterial({color:0x18271f,wireframe:true}));sculpture.add(frame);
const shards=new THREE.Group();sculpture.add(shards);for(let i=0;i<14;i++){const m=new THREE.Mesh(new THREE.BoxGeometry(.16,.5+(i%4)*.13,.16),new THREE.MeshStandardMaterial({color:colors[i%4],roughness:.6}));const a=i/14*Math.PI*2;m.position.set(Math.cos(a)*2.6,Math.sin(a)*2.6,Math.sin(a*3)*.55);m.rotation.z=a;shards.add(m);}
scene.add(new THREE.AmbientLight(0xffffff,2.4));const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(4,5,7);scene.add(light);
let pointer={x:0,y:0},active=true;const reduce=matchMedia('(prefers-reduced-motion: reduce)');host.querySelector('.art-fallback').hidden=true;
function resize(){const r=host.getBoundingClientRect();renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();renderer.render(scene,camera);}new ResizeObserver(resize).observe(host);
window.addEventListener('pointermove',e=>{const r=host.getBoundingClientRect();pointer.x=Math.max(-1,Math.min(1,(e.clientX-r.left)/r.width*2-1));pointer.y=Math.max(-1,Math.min(1,(e.clientY-r.top)/r.height*2-1));},{passive:true});host.addEventListener('pointerdown',()=>{core.rotation.x+=.5;},{passive:true});
new IntersectionObserver(e=>active=e[0].isIntersecting).observe(host);
let prev=0;function draw(t){requestAnimationFrame(draw);if(!active||document.hidden||t-prev<33)return;prev=t;if(!reduce.matches){sculpture.rotation.y=t*.00012+pointer.x*.25;sculpture.rotation.x=pointer.y*.18;core.rotation.z=t*.00019;shards.rotation.z=-t*.00005;}core.material.color.set(document.body.classList.contains('busy')?0xf5f0d4:0xfa836d);renderer.render(scene,camera);}resize();requestAnimationFrame(draw);
}catch(error){canvas.hidden=true;}
