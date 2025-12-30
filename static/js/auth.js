// Login form handler
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    const errorMsg = document.getElementById('errorMessage');
    
    // Show loading state
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-block';
    errorMsg.style.display = 'none';
    
    const formData = new FormData(form);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = result.redirect || '/';
        } else {
            errorMsg.textContent = result.error || 'Invalid credentials';
            errorMsg.style.display = 'block';
            submitBtn.disabled = false;
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
        }
    } catch (error) {
        errorMsg.textContent = 'An error occurred. Please try again.';
        errorMsg.style.display = 'block';
        submitBtn.disabled = false;
        btnText.style.display = 'inline-block';
        btnLoader.style.display = 'none';
    }
});

