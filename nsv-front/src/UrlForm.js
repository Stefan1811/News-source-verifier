import React, { useState } from 'react';
import './UrlForm.css'; 

function UrlForm() {
  const [url, setUrl] = useState('');
  const [articleData, setArticleData] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!url) {
      setErrorMessage('URL is required');
      setArticleData(null);
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
        setErrorMessage(`Error: ${errorData.error}`);
        setArticleData(null);
        return;
      }

      const responseData = await response.json();
      setArticleData(responseData); // Stocăm datele articolului
      setErrorMessage('');
    } catch (error) {
      setErrorMessage(`An error occurred: ${error.message}`);
      setArticleData(null);
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

      {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}

      {articleData && (
        <div className="article-details">
          <h2>Article Details</h2>
          <p><strong>Title:</strong> {articleData.title}</p>
          <p><strong>Author:</strong> {articleData.author}</p>
          <p><strong>Publish Date:</strong> {new Date(articleData.publish_date).toLocaleDateString()}</p>
          <p><strong>Status:</strong> {articleData.status}</p>
          <p><strong>Trust Score:</strong> {articleData.trust_score || 'N/A'}</p>
          <p><strong>Content Consistency:</strong> {articleData.content_consistency}</p>
          <p><strong>Sentiment Subjectivity:</strong> {articleData.sentiment_subjectivity}</p>
          <p><strong>URL:</strong> <a href={articleData.url} target="_blank" rel="noopener noreferrer">{articleData.url}</a></p>
        </div>
      )}
    </div>
  );
}

export default UrlForm;
