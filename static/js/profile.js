/* ==========================================================================
   NeuroSense AI — Profile Page
   Features:
   - Load profile
   - Save profile
   - Delete account
   - Upload profile photo
   - Crop profile photo with drag + zoom
   - Upload cropped avatar to /api/user/avatar
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    loadProfile();
    initProfileForm();
    initAvatarCropUpload();
    initDeleteAccount();
});

/* ==========================================================================
   LOAD PROFILE
   ========================================================================== */

async function loadProfile(){
    try{
        const res = await fetch("/api/user/profile", {
            method:"GET",
            headers:{
                "Accept":"application/json"
            }
        });

        const data = await safeJson(res);

        if(!res.ok || !(data.ok || data.success)){
            console.warn(data.error || "Profile not loaded");
            return;
        }

        const profile = data.profile || {};
        const usage = data.usage || {};

        setValue("full_name", profile.full_name || "");
        setValue("phone", profile.phone || "");
        setValue("preferred_language", profile.preferred_language || "en");
        setValue("emergency_contact_name", profile.emergency_contact_name || "");
        setValue("emergency_contact_phone", profile.emergency_contact_phone || "");
        setValue("wellness_notes", profile.wellness_notes || "");

        setText("profileName", profile.full_name || "User");
        setText("profileEmail", profile.email || "—");
        setText("profileRole", String(profile.role || "user").toUpperCase());

        const avatarPreview = document.getElementById("avatarPreview");

        if(profile.avatar_url && avatarPreview){
            avatarPreview.src = addCache(profile.avatar_url);
        }

        setText("dailyMessages", usage.daily_messages ?? 0);
        setText("reportsGenerated", usage.reports_generated ?? 0);
        setText("voiceMinutes", usage.voice_minutes ?? 0);

    }catch(err){
        console.error("Profile loading failed:", err);
        toast("Profile loading failed");
    }
}

/* ==========================================================================
   PROFILE SAVE
   ========================================================================== */

function initProfileForm(){
    const form = document.getElementById("profileForm");
    const saveBtn = document.getElementById("saveProfileBtn");

    if(!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            full_name:getValue("full_name"),
            phone:getValue("phone"),
            preferred_language:getValue("preferred_language"),
            emergency_contact_name:getValue("emergency_contact_name"),
            emergency_contact_phone:getValue("emergency_contact_phone"),
            wellness_notes:getValue("wellness_notes")
        };

        try{
            if(saveBtn){
                saveBtn.disabled = true;
                saveBtn.textContent = "Saving...";
            }

            const res = await fetch("/api/user/profile", {
                method:"POST",
                headers:{
                    "Content-Type":"application/json",
                    "Accept":"application/json"
                },
                body:JSON.stringify(payload)
            });

            const data = await safeJson(res);

            if(!res.ok || !(data.ok || data.success)){
                throw new Error(data.error || "Profile update failed");
            }

            toast("Profile updated successfully");
            await loadProfile();

        }catch(err){
            console.error("Profile update failed:", err);
            toast(err.message || "Profile update failed");
        }finally{
            if(saveBtn){
                saveBtn.disabled = false;
                saveBtn.textContent = "Save Profile";
            }
        }
    });
}

/* ==========================================================================
   AVATAR CROP STATE
   ========================================================================== */

let cropState = {
    file:null,
    image:null,
    objectUrl:null,

    scale:1,
    baseScale:1,
    x:0,
    y:0,

    dragging:false,
    startX:0,
    startY:0,
    startOffsetX:0,
    startOffsetY:0,

    naturalWidth:0,
    naturalHeight:0
};

/* ==========================================================================
   AVATAR CROP INIT
   ========================================================================== */

function initAvatarCropUpload(){
    const input = document.getElementById("avatarInput");
    const btn = document.getElementById("avatarBtn");

    const modal = document.getElementById("avatarCropModal");
    const cropImage = document.getElementById("cropImage");
    const cropStage = document.getElementById("cropStage");
    const cropZoom = document.getElementById("cropZoom");

    const cropCloseBtn = document.getElementById("cropCloseBtn");
    const cropCancelBtn = document.getElementById("cropCancelBtn");
    const cropResetBtn = document.getElementById("cropResetBtn");
    const cropSaveBtn = document.getElementById("cropSaveBtn");

    if(!input || !btn){
        console.warn("Avatar input/button missing.");
        return;
    }

    if(!modal || !cropImage || !cropStage || !cropZoom){
        console.warn("Crop modal elements missing.");
        return;
    }

    btn.addEventListener("click", () => {
        input.click();
    });

    input.addEventListener("change", () => {
        const file = input.files && input.files[0];

        if(!file) return;

        const allowedTypes = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp"
        ];

        if(!allowedTypes.includes(file.type)){
            toast("Please upload JPG, PNG, or WEBP image only");
            input.value = "";
            return;
        }

        if(file.size > 5 * 1024 * 1024){
            toast("Photo must be less than 5 MB");
            input.value = "";
            return;
        }

        openCropModal(file);
    });

    cropZoom.addEventListener("input", () => {
        cropState.scale = Number(cropZoom.value || 1);
        updateCropTransform();
        updateCropPreview();
    });

    cropStage.addEventListener("pointerdown", (e) => {
        cropState.dragging = true;

        try{
            cropStage.setPointerCapture(e.pointerId);
        }catch(err){}

        cropState.startX = e.clientX;
        cropState.startY = e.clientY;
        cropState.startOffsetX = cropState.x;
        cropState.startOffsetY = cropState.y;
    });

    cropStage.addEventListener("pointermove", (e) => {
        if(!cropState.dragging) return;

        cropState.x = cropState.startOffsetX + (e.clientX - cropState.startX);
        cropState.y = cropState.startOffsetY + (e.clientY - cropState.startY);

        clampCropPosition();
        updateCropTransform();
        updateCropPreview();
    });

    cropStage.addEventListener("pointerup", () => {
        cropState.dragging = false;
    });

    cropStage.addEventListener("pointercancel", () => {
        cropState.dragging = false;
    });

    cropStage.addEventListener("wheel", (e) => {
        e.preventDefault();

        const current = Number(cropZoom.value || 1);
        const next = Math.max(1, Math.min(3, current + (e.deltaY < 0 ? 0.08 : -0.08)));

        cropZoom.value = next.toFixed(2);
        cropState.scale = next;

        updateCropTransform();
        updateCropPreview();
    }, { passive:false });

    cropCloseBtn?.addEventListener("click", closeCropModal);
    cropCancelBtn?.addEventListener("click", closeCropModal);

    cropResetBtn?.addEventListener("click", () => {
        resetCropPosition();
        updateCropTransform();
        updateCropPreview();
    });

    cropSaveBtn?.addEventListener("click", uploadCroppedAvatar);
}

/* ==========================================================================
   OPEN / CLOSE CROP MODAL
   ========================================================================== */

function openCropModal(file){
    const modal = document.getElementById("avatarCropModal");
    const cropImage = document.getElementById("cropImage");
    const cropZoom = document.getElementById("cropZoom");

    if(!modal || !cropImage || !cropZoom) return;

    cleanupCropObjectUrl();

    cropState.file = file;
    cropState.objectUrl = URL.createObjectURL(file);

    cropImage.onload = () => {
        cropState.image = cropImage;
        cropState.naturalWidth = cropImage.naturalWidth;
        cropState.naturalHeight = cropImage.naturalHeight;

        cropZoom.value = "1";

        modal.classList.add("show");
        document.body.style.overflow = "hidden";

        /*
          Important:
          Modal must be visible before reading cropStage width/height.
          If calculated while hidden, image scale becomes 0 and image disappears.
        */
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                resetCropPosition();
                updateCropTransform();
                updateCropPreview();
            });
        });
    };

    cropImage.onerror = () => {
        toast("Could not load selected image. Please try another photo.");
        closeCropModal();
    };

    cropImage.src = cropState.objectUrl;
}

function closeCropModal(){
    const modal = document.getElementById("avatarCropModal");
    const input = document.getElementById("avatarInput");
    const cropImage = document.getElementById("cropImage");
    const preview = document.getElementById("cropFinalPreview");

    if(modal){
        modal.classList.remove("show");
    }

    document.body.style.overflow = "";

    if(input){
        input.value = "";
    }

    if(cropImage){
        cropImage.removeAttribute("src");
        cropImage.removeAttribute("style");
    }

    if(preview){
        preview.removeAttribute("src");
    }

    cleanupCropObjectUrl();

    cropState = {
        file:null,
        image:null,
        objectUrl:null,

        scale:1,
        baseScale:1,
        x:0,
        y:0,

        dragging:false,
        startX:0,
        startY:0,
        startOffsetX:0,
        startOffsetY:0,

        naturalWidth:0,
        naturalHeight:0
    };
}

function cleanupCropObjectUrl(){
    if(cropState.objectUrl){
        URL.revokeObjectURL(cropState.objectUrl);
    }
}

/* ==========================================================================
   CROP POSITION / TRANSFORM
   ========================================================================== */

function resetCropPosition(){
    const cropStage = document.getElementById("cropStage");
    const cropZoom = document.getElementById("cropZoom");
    const zoomValue = document.getElementById("zoomValue");

    if(!cropStage || !cropState.naturalWidth || !cropState.naturalHeight) return;

    const rect = cropStage.getBoundingClientRect();

    if(!rect.width || !rect.height){
        setTimeout(() => {
            resetCropPosition();
            updateCropTransform();
            updateCropPreview();
        }, 60);
        return;
    }

    const stageSize = Math.min(rect.width, rect.height);
    const ringSize = stageSize * 0.72;

    cropState.baseScale = Math.max(
        ringSize / cropState.naturalWidth,
        ringSize / cropState.naturalHeight
    );

    cropState.scale = 1;
    cropState.x = 0;
    cropState.y = 0;

    if(cropZoom){
        cropZoom.value = "1";
    }

    if(zoomValue){
        zoomValue.textContent = "100%";
    }
}

function updateCropTransform(){
    const cropImage = document.getElementById("cropImage");
    const zoomValue = document.getElementById("zoomValue");

    if(!cropImage || !cropState.naturalWidth || !cropState.naturalHeight) return;

    clampCropPosition();

    const finalScale = cropState.baseScale * cropState.scale;

    if(!finalScale) return;

    cropImage.style.width = `${cropState.naturalWidth}px`;
    cropImage.style.height = `${cropState.naturalHeight}px`;

    cropImage.style.transform = `
        translate(calc(-50% + ${cropState.x}px), calc(-50% + ${cropState.y}px))
        scale(${finalScale})
    `;

    if(zoomValue){
        zoomValue.textContent = `${Math.round(cropState.scale * 100)}%`;
    }
}

function clampCropPosition(){
    const cropStage = document.getElementById("cropStage");

    if(!cropStage || !cropState.naturalWidth || !cropState.naturalHeight) return;

    const rect = cropStage.getBoundingClientRect();

    if(!rect.width || !rect.height) return;

    const stageSize = Math.min(rect.width, rect.height);
    const ringSize = stageSize * 0.72;

    const finalScale = cropState.baseScale * cropState.scale;

    if(!finalScale) return;

    const displayedWidth = cropState.naturalWidth * finalScale;
    const displayedHeight = cropState.naturalHeight * finalScale;

    const maxX = Math.max(0, (displayedWidth - ringSize) / 2);
    const maxY = Math.max(0, (displayedHeight - ringSize) / 2);

    cropState.x = Math.max(-maxX, Math.min(maxX, cropState.x));
    cropState.y = Math.max(-maxY, Math.min(maxY, cropState.y));
}

/* ==========================================================================
   CROP PREVIEW + BLOB
   ========================================================================== */

let previewUrl = null;

async function updateCropPreview(){
    const preview = document.getElementById("cropFinalPreview");

    if(!preview) return;

    const blob = await createCroppedBlob(256);

    if(!blob) return;

    if(previewUrl){
        URL.revokeObjectURL(previewUrl);
    }

    previewUrl = URL.createObjectURL(blob);
    preview.src = previewUrl;
}

async function createCroppedBlob(size = 512){
    const cropStage = document.getElementById("cropStage");

    if(!cropStage || !cropState.image || !cropState.naturalWidth || !cropState.naturalHeight){
        return null;
    }

    const rect = cropStage.getBoundingClientRect();

    if(!rect.width || !rect.height){
        return null;
    }

    const stageSize = Math.min(rect.width, rect.height);
    const ringSize = stageSize * 0.72;

    const finalScale = cropState.baseScale * cropState.scale;

    if(!finalScale){
        return null;
    }

    /*
      The image is positioned at stage center + offsets.
      Convert ring crop area from stage coordinates to natural image coordinates.
    */
    const imageCenterX = rect.width / 2 + cropState.x;
    const imageCenterY = rect.height / 2 + cropState.y;

    const cropCenterX = rect.width / 2;
    const cropCenterY = rect.height / 2;

    const imageDisplayedWidth = cropState.naturalWidth * finalScale;
    const imageDisplayedHeight = cropState.naturalHeight * finalScale;

    const imageLeft = imageCenterX - imageDisplayedWidth / 2;
    const imageTop = imageCenterY - imageDisplayedHeight / 2;

    const cropLeft = cropCenterX - ringSize / 2;
    const cropTop = cropCenterY - ringSize / 2;

    const sourceX = (cropLeft - imageLeft) / finalScale;
    const sourceY = (cropTop - imageTop) / finalScale;
    const sourceSize = ringSize / finalScale;

    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;

    const ctx = canvas.getContext("2d");

    ctx.clearRect(0,0,size,size);

    ctx.save();
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();

    ctx.drawImage(
        cropState.image,
        sourceX,
        sourceY,
        sourceSize,
        sourceSize,
        0,
        0,
        size,
        size
    );

    ctx.restore();

    return new Promise((resolve) => {
        canvas.toBlob((blob) => {
            resolve(blob);
        }, "image/png", 0.95);
    });
}

/* ==========================================================================
   UPLOAD CROPPED AVATAR
   ========================================================================== */

async function uploadCroppedAvatar(){
    const cropSaveBtn = document.getElementById("cropSaveBtn");
    const avatarBtn = document.getElementById("avatarBtn");
    const avatarPreview = document.getElementById("avatarPreview");

    try{
        const blob = await createCroppedBlob(512);

        if(!blob){
            throw new Error("Could not crop image");
        }

        const fileName = `avatar_${Date.now()}.png`;

        const fd = new FormData();
        fd.append("avatar", blob, fileName);

        if(cropSaveBtn){
            cropSaveBtn.disabled = true;
            cropSaveBtn.textContent = "Saving...";
        }

        if(avatarBtn){
            avatarBtn.disabled = true;
            avatarBtn.textContent = "Uploading...";
        }

        toast("Uploading cropped photo...");

        const res = await fetch("/api/user/avatar", {
            method:"POST",
            body:fd
        });

        const data = await safeJson(res);

        if(!res.ok || !(data.ok || data.success)){
            throw new Error(data.error || "Photo upload failed");
        }

        const avatarUrl = data.avatar_url || data.url;

        if(!avatarUrl){
            throw new Error("Avatar uploaded but avatar_url was not returned by server");
        }

        if(avatarPreview){
            avatarPreview.src = addCache(avatarUrl);
        }

        closeCropModal();
        toast("Profile photo updated successfully");

        await loadProfile();

    }catch(err){
        console.error("Photo upload failed:", err);
        toast(err.message || "Photo upload failed");
    }finally{
        if(cropSaveBtn){
            cropSaveBtn.disabled = false;
            cropSaveBtn.textContent = "Save Cropped Photo";
        }

        if(avatarBtn){
            avatarBtn.disabled = false;
            avatarBtn.textContent = "Upload & Crop Profile Photo";
        }
    }
}

/* ==========================================================================
   DELETE ACCOUNT
   ========================================================================== */

function initDeleteAccount(){
    const btn = document.getElementById("deleteAccountBtn");

    if(!btn) return;

    btn.addEventListener("click", async () => {
        const confirmText = prompt("Type DELETE to confirm account deletion:");

        if(confirmText !== "DELETE"){
            toast("Account deletion cancelled");
            return;
        }

        try{
            btn.disabled = true;
            btn.textContent = "Deleting...";

            const res = await fetch("/api/user/delete_account", {
                method:"POST",
                headers:{
                    "Content-Type":"application/json",
                    "Accept":"application/json"
                },
                body:JSON.stringify({
                    confirm:"DELETE"
                })
            });

            const data = await safeJson(res);

            if(!res.ok || !(data.ok || data.success)){
                throw new Error(data.error || "Delete failed");
            }

            toast("Account deleted");

            setTimeout(() => {
                window.location.href = "/";
            }, 900);

        }catch(err){
            console.error("Delete failed:", err);
            toast(err.message || "Delete failed");

            btn.disabled = false;
            btn.textContent = "Delete Account";
        }
    });
}

/* ==========================================================================
   HELPERS
   ========================================================================== */

function getValue(id){
    const el = document.getElementById(id);
    return el ? String(el.value || "").trim() : "";
}

function setValue(id,value){
    const el = document.getElementById(id);
    if(el) el.value = value;
}

function setText(id,value){
    const el = document.getElementById(id);
    if(el) el.textContent = value;
}

async function safeJson(res){
    try{
        return await res.json();
    }catch(err){
        return {
            ok:false,
            success:false,
            error:"Invalid server response"
        };
    }
}

function addCache(url){
    if(!url) return url;

    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}t=${Date.now()}`;
}

function toast(message){
    const existing = document.querySelector(".profile-toast");

    if(existing){
        existing.remove();
    }

    const t = document.createElement("div");

    t.className = "profile-toast";
    t.textContent = message;

    document.body.appendChild(t);

    setTimeout(() => {
        t.style.opacity = "0";
        t.style.transform = "translateY(12px)";
        t.style.transition = ".25s";

        setTimeout(() => {
            if(t && t.parentNode){
                t.remove();
            }
        }, 300);
    }, 2800);
}