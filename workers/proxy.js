// NextAura Vault Proxy — routes app4.nextaura.fit to IBM Code Engine
// Preserves all headers, cookies, and paths

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Target: IBM Code Engine backend
    const target = new URL(
      url.pathname + url.search,
      'https://nextaura-vault.284w7l87aq94.us-south.codeengine.appdomain.cloud'
    );

    // Clone request with target URL
    const modified = new Request(target, request);

    // Forward to IBM backend
    const response = await fetch(modified, {
      redirect: 'manual',  // Don't follow redirects, pass them through
    });

    // Clone response so we can modify headers
    const newResponse = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });

    // Add security headers
    newResponse.headers.set('X-Content-Type-Options', 'nosniff');
    newResponse.headers.set('X-Frame-Options', 'DENY');
    newResponse.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

    return newResponse;
  },
};
