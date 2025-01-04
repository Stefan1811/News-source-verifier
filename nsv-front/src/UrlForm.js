import React, { useState } from 'react';
import './UrlForm.css'; // Import stiluri

function UrlForm() {
  const [url, setUrl] = useState('');
  const [responseMessage, setResponseMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!url) {
      setResponseMessage('URL is required');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:5000/articles/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setResponseMessage(`Error: ${errorData.error}`);
        return;
      }

      const responseData = await response.json();
      setResponseMessage(`Article created successfully: ${responseData.title}`);
    } catch (error) {
      setResponseMessage(`An error occurred: ${error.message}`);
    }
  };

  return (
    <div className="container">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter URL here"
        />
        <button type="submit">Submit</button>
      </form>
      {responseMessage && <p>{responseMessage}</p>}
    </div>
  );
}

export default UrlForm;
