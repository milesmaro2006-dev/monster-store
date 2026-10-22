(function () {
  'use strict';
  function start() {
    const mount = document.querySelector('[data-hero-viewer]');
    if (!mount || !window.THREE || !THREE.GLTFLoader) return;
    let specs;
    try { specs = JSON.parse(mount.dataset.models || '[]'); } catch (_) { return; }
    if (specs.length !== 1) return;
    const spec = specs[0];
    const loading = mount.querySelector('[data-viewer-loading]');
    const fallback = mount.querySelector('[data-viewer-fallback]');
    const image = mount.querySelector('[data-viewer-image]');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let renderer, scene, camera, can, frame = 0, visible = true, previous = 0, dead = false;
    const isMobile = window.matchMedia('(max-width: 767px)').matches;
    function showFallback(message) {
      if (loading) loading.hidden = true;
      if (fallback) fallback.hidden = false;
      const text = mount.querySelector('[data-viewer-message]');
      if (text) text.textContent = message;
    }
    function dispose() {
      dead = true;
      if (frame) cancelAnimationFrame(frame);
      if (can) can.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
        materials.filter(Boolean).forEach((mat) => {
          Object.values(mat).forEach((value) => { if (value && value.isTexture) value.dispose(); });
          mat.dispose();
        });
      });
      if (renderer) {
        renderer.dispose();
        if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement);
      }
    }
    function fit() {
      if (!renderer || !camera) return;
      const w = Math.max(mount.clientWidth, 1), h = Math.max(mount.clientHeight, 1);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobile ? 1 : 1.5));
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    function animate(time) {
      frame = 0;
      if (dead || !can || !visible || document.hidden) return;
      const dt = previous ? Math.min((time - previous) / 1000, .05) : 0;
      previous = time;
      if (!reduced) can.rotation.y += dt * 1.2;
      renderer.render(scene, camera);
      if (!reduced) frame = requestAnimationFrame(animate);
    }
    function draw() { if (!frame && visible && !document.hidden) frame = requestAnimationFrame(animate); }
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: !isMobile, powerPreference: 'low-power' });
      renderer.setClearColor(0x000000, 0);
      renderer.outputEncoding = THREE.sRGBEncoding;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.08;
      renderer.domElement.setAttribute('aria-hidden', 'true');
      mount.insertBefore(renderer.domElement, loading || fallback || null);
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(38, 1, .1, 100);
      camera.position.set(0, 0, 6.5);
      scene.add(new THREE.HemisphereLight(0xe8f5d0, 0x10140a, 1.4));
      const key = new THREE.DirectionalLight(0xffffff, 3); key.position.set(-3, 4, 5); scene.add(key);
      const fill = new THREE.DirectionalLight(0xb4ff00, 1.1); fill.position.set(4, 1, 2); scene.add(fill);
      fit();
      window.addEventListener('resize', fit, { passive: true });
      new THREE.GLTFLoader().load(spec.url, (gltf) => {
        if (dead) return;
        can = gltf.scene;
        const bounds = new THREE.Box3().setFromObject(can);
        const size = bounds.getSize(new THREE.Vector3());
        const center = bounds.getCenter(new THREE.Vector3());
        if (size.z > size.y * 1.2 && size.z > size.x) can.rotation.x = -Math.PI / 2;
        else if (size.x > size.y * 1.2 && size.x > size.z) can.rotation.z = Math.PI / 2;
        can.updateMatrixWorld(true);
        const fitted = new THREE.Box3().setFromObject(can);
        const extent = fitted.getSize(new THREE.Vector3());
        const midpoint = fitted.getCenter(new THREE.Vector3());
        can.scale.setScalar(2.8 / Math.max(extent.y, .001));
        can.position.set(-midpoint.x * can.scale.x, -midpoint.y * can.scale.y, -midpoint.z * can.scale.z);
        scene.add(can);
        if (loading) loading.hidden = true;
        if (fallback) fallback.hidden = true;
        const observer = new IntersectionObserver((entries) => {
          visible = entries[0].isIntersecting;
          if (visible) draw(); else { cancelAnimationFrame(frame); frame = 0; previous = 0; }
        }, { threshold: .01 });
        observer.observe(mount);
        window.addEventListener('pagehide', () => { observer.disconnect(); dispose(); }, { once: true });
        draw();
      }, undefined, (error) => {
        console.error('Unable to load the classic black-can model.', error);
        showFallback('يتعذر عرض العبوة ثلاثية الأبعاد في هذا المتصفح.');
      });
      renderer.domElement.addEventListener('webglcontextlost', (event) => { event.preventDefault(); showFallback('توقف العرض ثلاثي الأبعاد.'); });
    } catch (error) {
      console.error('Unable to initialize the 3D hero.', error);
      showFallback('يتعذر عرض العبوة ثلاثية الأبعاد في هذا المتصفح.');
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
