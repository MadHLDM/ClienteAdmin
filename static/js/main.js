/**
 * Admin Clientes - Frontend Enhancements
 * Progressive enhancement for better UX
 */

document.addEventListener('DOMContentLoaded', () => {
  // ==========================================
  // Form Input Enhancements
  // ==========================================

  // Auto-trim text inputs on submit
  for (const form of document.querySelectorAll('form')) {
    form.addEventListener('submit', (e) => {
      // If submission was prevented (e.g., by confirm cancel), do nothing
      if (e.defaultPrevented) return;
      form.querySelectorAll('input[type="text"]').forEach(input => {
        input.value = input.value.trim();
      });
    });
  }

  // Confirm clicks on elements marked with [data-confirm]
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-confirm]');
    if (!el) return;
    const msg = el.getAttribute('data-confirm') || 'Confirmar?';
    if (!window.confirm(msg)) {
      e.preventDefault();
      e.stopPropagation();
    }
  }, true);

  // ==========================================
  // Active Navigation Highlighting
  // ==========================================

  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.topbar nav a');

  navLinks.forEach(link => {
    const linkPath = new URL(link.href).pathname;
    if (currentPath.startsWith(linkPath) && linkPath !== '/') {
      link.style.color = 'var(--text-primary)';
      link.style.background = 'var(--bg-tertiary)';
    }
  });

  // ==========================================
  // Smooth Transitions for Flash Messages
  // ==========================================

  const flashMessages = document.querySelectorAll('.flash, .errors');
  flashMessages.forEach(flash => {
    flash.style.opacity = '0';
    flash.style.transform = 'translateY(-10px)';
    flash.style.transition = 'all 0.3s ease-out';

    setTimeout(() => {
      flash.style.opacity = '1';
      flash.style.transform = 'translateY(0)';
    }, 100);

    // Auto-dismiss flash messages after 5 seconds
    if (flash.classList.contains('flash')) {
      setTimeout(() => {
        flash.style.opacity = '0';
        flash.style.transform = 'translateY(-10px)';
        setTimeout(() => flash.remove(), 300);
      }, 5000);
    }
  });

  // ==========================================
  // CPF Input Formatting (Visual Only)
  // ==========================================

  const cpfInputs = document.querySelectorAll('input[name="cpf"]');
  cpfInputs.forEach(input => {
    input.addEventListener('input', (e) => {
      // Remove non-digits
      let value = e.target.value.replace(/\D/g, '');

      // Limit to 10 digits
      if (value.length > 10) {
        value = value.slice(0, 10);
      }

      e.target.value = value;
    });
  });

  // ==========================================
  // Form Field Focus Animation
  // ==========================================

  const formInputs = document.querySelectorAll('input, select, textarea');
  formInputs.forEach(input => {
    input.addEventListener('focus', function() {
      const field = this.closest('.field');
      if (field) {
        const label = field.querySelector('label');
        if (label) {
          label.style.color = 'var(--primary-light)';
          label.style.transition = 'color 0.15s ease';
        }
      }
    });

    input.addEventListener('blur', function() {
      const field = this.closest('.field');
      if (field) {
        const label = field.querySelector('label');
        if (label) {
          label.style.color = 'var(--text-secondary)';
        }
      }
    });
  });

  // ==========================================
  // Table Row Click Enhancement
  // ==========================================

  const tableRows = document.querySelectorAll('.table tbody tr');
  tableRows.forEach(row => {
    row.style.cursor = 'default';
  });

  // ==========================================
  // Keyboard Shortcuts
  // ==========================================

  document.addEventListener('keydown', (e) => {
    // Alt + N: New Client (on clients page)
    if (e.altKey && e.key === 'n' && currentPath.includes('/clients')) {
      e.preventDefault();
      const newBtn = document.querySelector('a[href="/clients/new"]');
      if (newBtn) newBtn.click();
    }

    // Alt + R: Reports page
    if (e.altKey && e.key === 'r') {
      e.preventDefault();
      window.location.href = '/reports';
    }

    // Alt + C: Clients page
    if (e.altKey && e.key === 'c') {
      e.preventDefault();
      window.location.href = '/clients';
    }
  });

  // ==========================================
  // Search Input Focus on Load
  // ==========================================

  const searchInput = document.querySelector('.search input[name="q"]');
  if (searchInput && !searchInput.value) {
    setTimeout(() => searchInput.focus(), 100);
  }

  // ==========================================
  // Loading State for Forms
  // ==========================================

  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      if (e.defaultPrevented) return;
      const submitBtn = this.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.6';
        submitBtn.style.cursor = 'not-allowed';

        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Processando...';

        // Re-enable if form validation fails
        setTimeout(() => {
          if (!this.checkValidity()) {
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
            submitBtn.style.cursor = 'pointer';
            submitBtn.textContent = originalText;
          }
        }, 100);
      }
    });
  });

  // ==========================================
  // Animate Cards on Reports Page
  // ==========================================

  const cards = document.querySelectorAll('.card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'all 0.4s ease-out';

    setTimeout(() => {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 100 + (index * 100));
  });

  // ==========================================
  // Console Welcome Message
  // ==========================================

  console.log('%cAdmin Clientes', 'font-size: 24px; font-weight: bold; color: #3b82f6;');
  console.log('%cSistema de Gerenciamento Profissional', 'font-size: 12px; color: #94a3b8;');
  console.log('%c\nAtalhos de Teclado:', 'font-size: 14px; font-weight: bold; color: #cbd5e1; margin-top: 10px;');
  console.log('%cAlt + N → Novo Cliente', 'color: #94a3b8;');
  console.log('%cAlt + C → Página de Clientes', 'color: #94a3b8;');
  console.log('%cAlt + R → Relatórios', 'color: #94a3b8;');
});
