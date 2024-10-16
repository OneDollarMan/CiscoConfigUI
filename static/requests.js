function openModal(id) {
    document.getElementById(id).style.display = "block";
}

function closeModal(id) {
    document.getElementById(id).style.display = "none";
}

async function sendJsonQuery(address, method, data) {
    const res = await fetch(address, {
        method: method,
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    return res
}

async function loginUser() {
    var params = new URLSearchParams();
    params.set('username', document.getElementById('loginEmail').value);
    params.set('password', document.getElementById('loginPassword').value);

    const res = await fetch('/api/auth/jwt/login', {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: params
    })
    if (res.ok) {
        window.location.replace("/devices");
    }
}

async function registerUser() {
    data = {
        email: document.getElementById('email').value,
        username: document.getElementById('username').value,
        putty_login: document.getElementById('putty_login').value,
        putty_password: document.getElementById('putty_password').value,
        password: document.getElementById('password').value,
    }

    const res = await fetch('/api/auth/register', {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })

    if (res.ok) {
        closeModal('modalSignup');
        openModal('modalSignin');
    }
}

async function logoutUser() {
    const res = await fetch('/api/auth/jwt/logout', {
        method: "POST",
    })
    if (res.ok) {
        window.location.replace("/");
    }
}

async function addDevice(event) {
    event.preventDefault()
    const formData = new FormData(event.target);
    data = {
        name: formData.get('name'),
        ip_address: formData.get('ip_address'),
    }

    const res = await sendJsonQuery('/api/devices', "POST", data)

    if (res.ok) {
        var device = await res.json()
        formData.delete('name')
        formData.delete('ip_address')
        const configRes = await fetch(`/api/devices/${device.id}/upload_config`, {
            method: 'POST',
            body: formData,
        });
        if (configRes.ok) {
            window.location.replace("/devices");
        }
    }
}

async function updateDeviceConfig(event, deviceId) {
    event.preventDefault()
    const formData = new FormData(event.target);
    const configRes = await fetch(`/api/devices/${deviceId}/upload_config`, {
        method: 'POST',
        body: formData,
    });
    if (configRes.ok) {
        window.location.replace(`/devices/${deviceId}`);
    }
}

async function downloadDeviceConfig(deviceId) {
    window.location.replace(`/api/devices/${deviceId}/download_config`);
}

async function deleteDevice(event, deviceId) {
    event.stopPropagation();

    const res = await fetch(`/api/devices/${deviceId}`, {
        method: "DELETE",
    })
    if (res.ok) {
        window.location.replace("/devices");
    }
}

async function compareConfigs(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    if (formData.get('device1_id') && formData.get('device2_id')) {
        window.location.replace(`/compare?device1_id=${formData.get('device1_id')}&device2_id=${formData.get('device2_id')}`);
    }
}