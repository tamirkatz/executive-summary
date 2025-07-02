export const colorAnimation = `
@keyframes modernColorFlow {
  0% { stroke: #2563eb; }
  20% { stroke: #4f46e5; }
  40% { stroke: #7c3aed; }
  60% { stroke: #6366f1; }
  80% { stroke: #3b82f6; }
  100% { stroke: #2563eb; }
}

@keyframes subtleFloat {
  0%, 100% { 
    transform: translateY(0px);
    opacity: 0.8;
  }
  50% { 
    transform: translateY(-10px);
    opacity: 1;
  }
}

@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.animate-modern-colors {
  animation: modernColorFlow 6s ease-in-out infinite;
}

.animate-float {
  animation: subtleFloat 4s ease-in-out infinite;
}

.shimmer {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.1) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  background-size: 1000px 100%;
  animation: shimmer 3s infinite linear;
}

.loader-icon {
  transition: stroke 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
`;

export const dmSansStyle = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&family=Inter:wght@300;400;500;600;700;800&display=swap');
  
  body {
    font-family: 'Inter', 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  }
`;

export const glassStyle = {
  base: "bg-white/95 border border-gray-100 shadow-sm",
  card: "bg-white/98 border border-gray-100 shadow-md rounded-2xl p-8 hover:shadow-lg transition-shadow duration-300",
  input:
    "bg-white/95 border border-gray-100 shadow-sm pl-12 w-full rounded-xl py-3 px-4 text-gray-900 focus:border-blue-400/50 focus:outline-none focus:ring-2 focus:ring-blue-400/30 placeholder-gray-500 transition-all duration-300",
};

export const fadeInAnimation = {
  fadeIn: "transition-all duration-500 ease-out transform",
  writing: "animate-pulse",
  colorTransition: colorAnimation,
};
