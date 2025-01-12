import React, { useState, useEffect } from 'react';
import './UrlForm.css';

function UrlForm() {
  const [url, setUrl] = useState('');
  const [articleData, setArticleData] = useState(null);
  const [recentArticles, setRecentArticles] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [articleDataModalOpen, setArticleDataModalOpen] = useState(false);

  const ContentWithNewLines = ({ content }) => {
    return content.split('\n').map((line, index) => (
      <p key={index}>{line}</p>
    ));
  };

  const [detailsVisible, setDetailsVisible] = useState(false);

  const toggleDetails = () => {
    setDetailsVisible(!detailsVisible);
  };

  useEffect(() => {
    const fetchRecentArticles = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/latest-articles');
        if (!response.ok) {
          throw new Error('Failed to fetch');
        }
        const data = await response.json();
        setRecentArticles(data);
      } catch (error) {
        console.error('Failed to fetch recent articles', error);
      }
    };

    fetchRecentArticles();
  }, []);

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
      setArticleData(responseData);
      setErrorMessage('');
      setArticleDataModalOpen(true); // Open the modal for articleData
    } catch (error) {
      setErrorMessage(`An error occurred: ${error.message}`);
      setArticleData(null);
    }
  };

  const handleIconClick = (article) => {
    setSelectedArticle(article);
    setModalIsOpen(true);
  };

  const closeArticleDataModal = () => {
    setArticleDataModalOpen(false);
    window.location.reload(); // Refresh the page when closing articleData modal
  };

  const closeSelectedArticleModal = () => {
    setModalIsOpen(false); // Just close the modal for existing articles
  };

  const renderModalContent = (data, closeModalHandler) => (
    <div className="modal-content">
      <button className="close-button" onClick={closeModalHandler}>
        <i className="fas fa-times"></i>
      </button>
      <h2>
        <a href={data.url} target="_blank" rel="noopener noreferrer">
          {data.title}
          <i className="fas fa-link" style={{ marginLeft: '8px' }}></i>
        </a>
      </h2>
      <hr className="custom-line" />

      <div className="info-row">
        <div className="label">
          <i className="fas fa-user"></i>
          <span>{data.author}</span>
        </div>
        <div className="label">
          <i className="fas fa-calendar-alt"></i>
          <span>{new Date(data.publish_date).toLocaleDateString()}</span>
        </div>
        <div
          className="label"
          onClick={() => setDetailsVisible(!detailsVisible)}
          style={{
            position: 'relative',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <i
              className={`fas ${
                data.trust_score >= 0.5 ? 'fa-check-circle' : 'fa-times-circle'
              }`}
              style={{
                color: data.trust_score >= 0.5 ? 'green' : 'red',
                marginRight: '8px',
              }}
            ></i>
            <span>
              {data.trust_score !== null
                ? data.trust_score.toFixed(2)
                : 'N/A'}
            </span>
          </div>
          <i
            className={`fas fa-chevron-${detailsVisible ? 'up' : 'down'}`}
            style={{
              color: '#666',
              marginLeft: '10px',
            }}
          ></i>

          {detailsVisible && (
            <div
              className="details-popup"
              style={{
                position: 'absolute',
                zIndex: 1000,
                top: '100%',
                left: 0,
                backgroundColor: '#fff',
                padding: '10px',
                boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)',
                borderRadius: '8px',
                width: '300px',
              }}
            >
              <p className="details-row">
                <i className="fas fa-balance-scale"></i>
                <strong>Content Consistency:</strong> {data.content_consistency}
              </p>
              <p className="details-row">
                <i className="fas fa-robot"></i>
                <strong>ML Model Prediction:</strong>{' '}
                {data.ml_model_prediction.toFixed(2)}
              </p>
              <p className="details-row">
                <i className="fas fa-chart-line"></i>
                <strong>Sentiment Subjectivity:</strong>{' '}
                {data.sentiment_subjectivity.toFixed(3)}
              </p>
            </div>
          )}
        </div>
      </div>
      <hr className="custom-line" />
      <div className="article-content">
        <ContentWithNewLines content={data.content} />
      </div>
    </div>
  );

  return (
    <div className="container">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter URL here"
        />
        <button type="submit" className="submit-button">
          Submit
        </button>
      </form>

      {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}

      <div className="recent-articles">
        {recentArticles.map((article) => (
          <div className="recent-article" key={article.article_id}>
            <h3>{article.title}</h3>
            <i
              className="fas fa-external-link-alt"
              onClick={() => handleIconClick(article)}
            ></i>
          </div>
        ))}
      </div>

      {modalIsOpen && selectedArticle && (
        <div className="modal-overlay">
          {renderModalContent(selectedArticle, closeSelectedArticleModal)}
        </div>
      )}

      {articleDataModalOpen && articleData && (
        <div className="modal-overlay">
          {renderModalContent(articleData, closeArticleDataModal)}
        </div>
      )}
    </div>
  );
}

export default UrlForm;
