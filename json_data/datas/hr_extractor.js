const fs = require('fs');

fs.readFile('web.whatsapp.com.har', 'utf8', (err, data) => {
  if (err) {
    console.error('Error reading HAR file:', err);
    return;
  }

  try {
    const har = JSON.parse(data);

    const catalogResponses = har.log.entries
      .filter(entry => entry.response.content.mimeType === 'application/json')
      .map(entry => {
        let responseContent = entry.response.content.text;

        // Check if content exists and is a valid JSON string
        if (responseContent && responseContent !== 'undefined') {
          try {
            responseContent = JSON.parse(responseContent); // Try to parse as JSON
          } catch (parseError) {
            console.warn(`Skipping invalid JSON at ${entry.request.url}`);
            responseContent = {}; // Or handle as needed
          }
        } else {
          console.warn(`No content or invalid content at ${entry.request.url}`);
          responseContent = {}; // Or handle as needed
        }

        return {
          url: entry.request.url,
          response: responseContent,
        };
      });

    // Save catalog responses to a new JSON file
    fs.writeFile('catalog_responses.json', JSON.stringify(catalogResponses, null, 2), err => {
      if (err) {
        console.error('Error saving catalog responses:', err);
      } else {
        console.log('Catalog responses saved to catalog_responses.json');
      }
    });

  } catch (parseError) {
    console.error('Error parsing HAR file:', parseError);
  }
});
