const https = require('https');

const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbwfSphaxGLWoQmV4z6nLNejjqFF8vWku2wLImZldN0JGCFwdzzYsZSVGv2-CNkaE6Gh/exec';

function getLocationData(ip) {
  return new Promise((resolve) => {
    if (!ip || ip === 'unknown' || ip.includes('::') || ip.startsWith('192.168') || ip.startsWith('10.')) {
      resolve({});
      return;
    }

    https.get(`https://ip-api.com/json/${ip}?fields=66846719`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve({});
        }
      });
    }).on('error', () => resolve({}));
  });
}

function saveToGoogleSheets(data) {
  return new Promise((resolve, reject) => {
    const url = new URL(GOOGLE_SCRIPT_URL);
    const postData = JSON.stringify(data);
    
    const options = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      },
      followRedirect: true
    };

    const req = https.request(options, (res) => {
      // Handle redirects
      if (res.statusCode === 302 || res.statusCode === 301) {
        https.get(res.headers.location, (redirectRes) => {
          let responseData = '';
          redirectRes.on('data', chunk => responseData += chunk);
          redirectRes.on('end', () => resolve(responseData));
        }).on('error', reject);
      } else {
        let responseData = '';
        res.on('data', chunk => responseData += chunk);
        res.on('end', () => resolve(responseData));
      }
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  try {
    const clientData = JSON.parse(event.body);
    
    const ip = (
      event.headers['x-real-ip'] ||
      event.headers['cf-connecting-ip'] ||
      event.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
      'unknown'
    );
    
    const location = await getLocationData(ip);
    
    const trackingData = {
      timestamp: new Date().toISOString(),
      ip_address: ip,
      city: location.city || 'Unknown',
      country: location.country || 'Unknown',
      region: location.regionName || 'Unknown',
      timezone: location.timezone || 'Unknown',
      isp: location.isp || 'Unknown',
      browser_name: detectBrowser(event.headers['user-agent'] || ''),
      os_name: detectOS(event.headers['user-agent'] || ''),
      device_type: clientData.device_type || (clientData.is_mobile ? 'Mobile' : 'Desktop'),
      screen_resolution: clientData.screen_resolution || 'Unknown',
      page_title: clientData.page_title || '',
      page_url: clientData.page_url || '',
      referrer: clientData.referrer || 'Direct',
      session_id: clientData.session_id || '',
      visitor_id: clientData.visitor_id || '',
      time_on_page: clientData.time_on_page || 0,
      user_agent: event.headers['user-agent'] || ''
    };

    // Save to Google Sheets
    await saveToGoogleSheets(trackingData);

    console.log('✅ Saved to Google Sheets:', trackingData.ip_address, trackingData.city);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        success: true, 
        location: `${location.city || 'Unknown'}, ${location.country || 'Unknown'}` 
      })
    };
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};

function detectBrowser(ua) {
  if (ua.includes('Edg')) return 'Edge';
  if (ua.includes('Chrome')) return 'Chrome';
  if (ua.includes('Safari') && !ua.includes('Chrome')) return 'Safari';
  if (ua.includes('Firefox')) return 'Firefox';
  if (ua.includes('Opera') || ua.includes('OPR')) return 'Opera';
  return 'Unknown';
}

function detectOS(ua) {
  if (ua.includes('Windows NT 10')) return 'Windows 10';
  if (ua.includes('Windows NT 6.3')) return 'Windows 8.1';
  if (ua.includes('Mac OS X')) return 'macOS';
  if (ua.includes('Android')) return 'Android';
  if (ua.includes('Linux')) return 'Linux';
  if (ua.includes('iPhone') || ua.includes('iPad')) return 'iOS';
  return 'Unknown';
}
