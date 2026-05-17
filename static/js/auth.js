/* ==========================================================================
   NeuroSense AI — Authentication
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {

  initPasswordToggle();
  initFormValidation();
  initAuthAnimations();
  initSocialButtons();
  initRememberMe();
  initAuthTabs();
  initFloatingBackground();
  initLoadingButtons();

});

/* ==========================================================================
   PASSWORD TOGGLE
   ========================================================================== */

function initPasswordToggle(){

  const toggles =
    document.querySelectorAll(
      ".password-toggle"
    );

  toggles.forEach((toggle) => {

    toggle.addEventListener("click", () => {

      const input =
        toggle.parentElement.querySelector(
          "input"
        );

      if(!input) return;

      if(input.type === "password"){

        input.type = "text";

        toggle.innerHTML = "🙈";

      }else{

        input.type = "password";

        toggle.innerHTML = "👁";

      }

    });

  });

}

/* ==========================================================================
   FORM VALIDATION
   ========================================================================== */

function initFormValidation(){

  const forms =
    document.querySelectorAll("form");

  forms.forEach((form) => {

    form.addEventListener("submit", async (e) => {

      e.preventDefault();

      clearErrors(form);

      const isValid =
        validateForm(form);

      if(!isValid) return;

      const submitBtn =
        form.querySelector(
          'button[type="submit"]'
        );

      setButtonLoading(submitBtn,true);

      try{

        await fakeRequest();

        showToast(
          "Authentication successful"
        );

        setTimeout(() => {

          window.location.href =
            "/dashboard";

        },1200);

      }catch(err){

        showError(
          form,
          "Authentication failed"
        );

      }finally{

        setButtonLoading(
          submitBtn,
          false
        );

      }

    });

  });

}

function validateForm(form){

  let valid = true;

  const email =
    form.querySelector(
      'input[type="email"]'
    );

  const password =
    form.querySelector(
      'input[type="password"]'
    );

  const fullname =
    form.querySelector(
      'input[name="fullname"]'
    );

  if(fullname){

    if(fullname.value.trim().length < 3){

      setFieldError(
        fullname,
        "Name must be at least 3 characters"
      );

      valid = false;
    }

  }

  if(email){

    const regex =
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if(!regex.test(email.value.trim())){

      setFieldError(
        email,
        "Enter a valid email address"
      );

      valid = false;
    }

  }

  if(password){

    if(password.value.length < 6){

      setFieldError(
        password,
        "Password must be at least 6 characters"
      );

      valid = false;
    }

  }

  return valid;

}

function setFieldError(input,message){

  input.style.borderColor =
    "#ff5d7a";

  const error =
    document.createElement("small");

  error.className = "field-error";

  error.style.color = "#ff91a6";

  error.style.marginTop = ".35rem";

  error.style.display = "block";

  error.textContent = message;

  input.parentElement.appendChild(error);

}

function clearErrors(form){

  form
    .querySelectorAll(".field-error")
    .forEach((e)=>e.remove());

  form
    .querySelectorAll("input")
    .forEach((input)=>{

      input.style.borderColor =
        "rgba(255,255,255,.06)";

    });

}

function showError(form,message){

  let alert =
    form.querySelector(".alert");

  if(!alert){

    alert =
      document.createElement("div");

    alert.className =
      "alert show";

    form.prepend(alert);

  }

  alert.textContent = message;

}

/* ==========================================================================
   BUTTON LOADING
   ========================================================================== */

function setButtonLoading(button,state){

  if(!button) return;

  if(state){

    button.disabled = true;

    button.dataset.original =
      button.innerHTML;

    button.innerHTML = `
      <div class="loader"></div>
    `;

  }else{

    button.disabled = false;

    button.innerHTML =
      button.dataset.original;
  }

}

function initLoadingButtons(){

  document
    .querySelectorAll(".social-btn")
    .forEach((btn)=>{

      btn.addEventListener("click",()=>{

        setButtonLoading(btn,true);

        setTimeout(()=>{

          setButtonLoading(btn,false);

          showToast(
            "OAuth integration coming soon"
          );

        },1500);

      });

    });

}

/* ==========================================================================
   ANIMATIONS
   ========================================================================== */

function initAuthAnimations(){

  const cards =
    document.querySelectorAll(
      ".auth-right, .auth-left"
    );

  cards.forEach((card,index)=>{

    card.style.opacity = "0";

    card.style.transform =
      "translateY(40px)";

    setTimeout(()=>{

      card.style.transition =
        "all .8s ease";

      card.style.opacity = "1";

      card.style.transform =
        "translateY(0px)";

    }, index * 150);

  });

}

/* ==========================================================================
   SOCIAL BUTTONS
   ========================================================================== */

function initSocialButtons(){

  document
    .querySelectorAll(".social-btn")
    .forEach((btn)=>{

      btn.addEventListener("mouseenter",()=>{

        btn.style.transform =
          "translateY(-3px)";

      });

      btn.addEventListener("mouseleave",()=>{

        btn.style.transform =
          "translateY(0px)";

      });

    });

}

/* ==========================================================================
   REMEMBER ME
   ========================================================================== */

function initRememberMe(){

  const remember =
    document.querySelector(
      "#rememberMe"
    );

  if(!remember) return;

  const stored =
    localStorage.getItem(
      "neurosense_remember"
    );

  if(stored === "true"){

    remember.checked = true;

  }

  remember.addEventListener("change",()=>{

    localStorage.setItem(
      "neurosense_remember",
      remember.checked
    );

  });

}

/* ==========================================================================
   AUTH TABS
   ========================================================================== */

function initAuthTabs(){

  const tabs =
    document.querySelectorAll(
      ".auth-tab"
    );

  if(!tabs.length) return;

  tabs.forEach((tab)=>{

    tab.addEventListener("click",()=>{

      tabs.forEach((t)=>{

        t.classList.remove("active");

      });

      tab.classList.add("active");

      const target =
        tab.dataset.target;

      document
        .querySelectorAll(".auth-panel")
        .forEach((panel)=>{

          panel.style.display = "none";

        });

      const activePanel =
        document.getElementById(target);

      if(activePanel){

        activePanel.style.display =
          "block";
      }

    });

  });

}

/* ==========================================================================
   FLOATING BACKGROUND
   ========================================================================== */

function initFloatingBackground(){

  const blobs =
    document.querySelectorAll(
      ".bg-blur"
    );

  if(!blobs.length) return;

  document.addEventListener(
    "mousemove",
    (e)=>{

      const x =
        e.clientX / window.innerWidth;

      const y =
        e.clientY / window.innerHeight;

      blobs.forEach((blob,index)=>{

        const speed =
          (index + 1) * 18;

        blob.style.transform =
          `translate(${x * speed}px, ${y * speed}px)`;

      });

    }
  );

}

/* ==========================================================================
   TOAST
   ========================================================================== */

function showToast(message){

  const toast =
    document.createElement("div");

  toast.className = "toast";

  toast.innerHTML = `
    <div style="
      font-weight:800;
      margin-bottom:.2rem
    ">
      NeuroSense AI
    </div>

    <div style="
      color:#aeb6d4;
      font-size:.9rem
    ">
      ${message}
    </div>
  `;

  toast.style.position = "fixed";

  toast.style.right = "24px";

  toast.style.bottom = "24px";

  toast.style.padding =
    "1rem 1.2rem";

  toast.style.borderRadius =
    "18px";

  toast.style.background =
    "rgba(20,24,39,.95)";

  toast.style.border =
    "1px solid rgba(255,255,255,.08)";

  toast.style.boxShadow =
    "0 25px 70px rgba(0,0,0,.45)";

  toast.style.zIndex = "9999";

  toast.style.animation =
    "toastIn .3s ease";

  document.body.appendChild(toast);

  setTimeout(()=>{

    toast.style.opacity = "0";

    toast.style.transform =
      "translateY(15px)";

    setTimeout(()=>{

      toast.remove();

    },300);

  },3000);

}

/* ==========================================================================
   FAKE REQUEST
   ========================================================================== */

function fakeRequest(){

  return new Promise((resolve)=>{

    setTimeout(resolve,1500);

  });

}

/* ==========================================================================
   ENTER KEY
   ========================================================================== */

document
  .querySelectorAll("input")
  .forEach((input)=>{

    input.addEventListener(
      "keypress",
      (e)=>{

        if(e.key === "Enter"){

          const form =
            input.closest("form");

          if(form){

            form.dispatchEvent(
              new Event("submit")
            );
          }

        }

      }
    );

  });

/* ==========================================================================
   INPUT EFFECTS
   ========================================================================== */

document
  .querySelectorAll(".auth-input")
  .forEach((input)=>{

    input.addEventListener(
      "focus",
      ()=>{

        input.parentElement.style.transform =
          "translateY(-2px)";
      }
    );

    input.addEventListener(
      "blur",
      ()=>{

        input.parentElement.style.transform =
          "translateY(0px)";
      }
    );

  });

/* ==========================================================================
   PASSWORD STRENGTH
   ========================================================================== */

const passwordField =
document.querySelector(
  'input[type="password"]'
);

if(passwordField){

  passwordField.addEventListener(
    "input",
    ()=>{

      const value =
        passwordField.value;

      let strength = 0;

      if(value.length >= 6) strength++;
      if(/[A-Z]/.test(value)) strength++;
      if(/[0-9]/.test(value)) strength++;
      if(/[^A-Za-z0-9]/.test(value)) strength++;

      updateStrength(strength);

    }
  );

}

function updateStrength(level){

  const meter =
    document.querySelector(
      ".password-strength"
    );

  if(!meter) return;

  const colors = [
    "#ff5d7a",
    "#ffc857",
    "#4fd1ff",
    "#00e5aa"
  ];

  meter.style.width =
    `${level * 25}%`;

  meter.style.background =
    colors[level - 1] || "#2d3550";

}