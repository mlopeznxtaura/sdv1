// NextAura Proxy — routes *.nextaura.fit subdomains to IBM Code Engine apps
// Preserves all headers, cookies, and paths
const CE_DOMAIN = '284w7l87aq94.us-south.codeengine.appdomain.cloud';

const BACKENDS = {
  'app2.nextaura.fit':        'nextaura-app2-v3l1',
  'app3.nextaura.fit':        'app3-nextaura-fit',
  'app4.nextaura.fit':        'nextaura-vault',
  'app5.nextaura.fit':        'app5-nextaura-fit',
  'app6.nextaura.fit':        'app6-nextaura-fit',
  'app7.nextaura.fit':        'app7-nextaura-fit',
  'app8.nextaura.fit':        'app8-nextaura-fit',
  'qvrmv3.nextaura.fit':      'nextaura-qvrmv3',
  'stage-shell.nextaura.fit': 'nextaura-stage-shell',
  'stage1.nextaura.fit':      'nextaura-stage1-capture',
  'stage2.nextaura.fit':      'nextaura-stage2-hypothesis',
  'v21all.nextaura.fit':      'v21all-app2',
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    let backend = BACKENDS[url.hostname];
    let pathname = url.pathname;

    // app4 integration: /depguard/* → sdv1-depguard app (prefix stripped)
    if (url.hostname === 'app4.nextaura.fit' &&
        (pathname === '/depguard' || pathname.startsWith('/depguard/'))) {
      backend = 'sdv1-depguard';
      pathname = pathname.slice('/depguard'.length) || '/';
    }

    if (!backend) {
      return new Response('Unknown host', { status: 404 });
    }

    const target = new URL(
      pathname + url.search,
      `https://${backend}.${CE_DOMAIN}`
    );

    // Clone request with target URL — preserves method, headers, cookies, body
    const modified = new Request(target, request);

    const response = await fetch(modified, {
      redirect: 'manual', // Don't follow redirects, pass them through
    });

    const newResponse = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });

    newResponse.headers.set('X-Content-Type-Options', 'nosniff');
    newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

    return newResponse;
  },
};
