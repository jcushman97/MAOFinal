// Interactive button functionality
document.querySelectorAll('.button').forEach(button => {
  button.addEventListener('click', function() {
    this.setAttribute('aria-pressed', 'true');
    this.classList.add('active');
    setTimeout(() => {
      this.setAttribute('aria-pressed', 'false');
      this.classList.remove('active');
    }, 200);
  });
});

// Interactive hover effects
document.querySelectorAll('.hover-effect').forEach(element => {
  element.addEventListener('mouseenter', function() {
    this.classList.add('hovered');
  });
  
  element.addEventListener('mouseleave', function() {
    this.classList.remove('hovered');
  });
});

// Form validation
const validateForm = (form) => {
  const inputs = form.querySelectorAll('input[required]');
  let isValid = true;

  inputs.forEach(input => {
    if (!input.value.trim()) {
      isValid = false;
      input.classList.add('error');
    } else {
      input.classList.remove('error');
    }
  });

  return isValid;
};

document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', function(e) {
    if (!validateForm(this)) {
      e.preventDefault();
      alert('Please fill in all required fields');
    }
  });
});

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// Enhanced performance measurement
const measurePerformance = () => {
  if ('performance' in window) {
    const navigation = performance.getEntriesByType('navigation')[0];
    if (navigation) {
      const metrics = {
        domLoading: Math.round(navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart),
        pageLoad: Math.round(navigation.loadEventEnd - navigation.loadEventStart),
        totalTime: Math.round(navigation.loadEventEnd - navigation.fetchStart),
        firstByte: Math.round(navigation.responseStart - navigation.fetchStart)
      };
      
      // Store metrics for debugging
      window.performanceMetrics = metrics;
      
      return metrics;
    }
  }
  return null;
};

// Measure performance after page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(measurePerformance, 100);
  });
} else {
  setTimeout(measurePerformance, 100);
}