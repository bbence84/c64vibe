const script = document.createElement('script');
script.src = 'https://www.googletagmanager.com/gtag/js?id=G-4S7FCDC77Z'; // URL of the remote file
script.onload = () => {
  console.log('Analytics script loaded successfully.');
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-4S7FCDC77Z');  
};
script.onerror = () => {
  console.error('Error loading analytics script.');
};
document.head.appendChild(script);