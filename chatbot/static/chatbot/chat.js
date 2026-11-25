(function () {
  "use strict";

  const chat = document.getElementById("chat");
  const buttons = document.getElementById("buttons");
  const typing = document.getElementById("typing");
  const csrfToken = document.querySelector("#csrf-form input[name=csrfmiddlewaretoken]").value;

  let currentStepCode = null;
  let busy = false;

  function scrollToBottom() {
    chat.scrollTop = chat.scrollHeight;
  }

  function postJSON(url, body) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify(body),
    }).then((response) => {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    });
  }

  function bubble(isUser, html) {
    const wrapper = document.createElement("div");
    wrapper.className = "msg" + (isUser ? " user" : "");

    const avatar = document.createElement("div");
    avatar.className = "avatar" + (isUser ? " user" : "");
    avatar.textContent = isUser ? "🙋" : "🏦";

    const body = document.createElement("div");
    body.className = "bubble";
    body.innerHTML = html;

    wrapper.appendChild(avatar);
    wrapper.appendChild(body);
    return wrapper;
  }

  function addMessage(isUser, html) {
    chat.appendChild(bubble(isUser, html));
    scrollToBottom();
  }

  function addImage(container, url) {
    if (!url) return;
    const img = document.createElement("img");
    img.src = url;
    img.alt = "Иллюстрация";
    img.loading = "lazy";
    container.appendChild(img);
  }

  function renderStep(step) {
    const wrapper = bubble(false, step.text);
    addImage(wrapper.querySelector(".bubble"), step.image_url);

    if (step.is_final && step.google_form_url) {
      const link = document.createElement("a");
      link.href = step.google_form_url;
      link.target = "_blank";
      link.rel = "noopener";
      link.className = "btn btn-success w-100 mt-3 fw-semibold";
      link.textContent = "📝 Заполнить анкету (Google Форма)";
      wrapper.querySelector(".bubble").appendChild(link);
    }

    chat.appendChild(wrapper);
    scrollToBottom();

    currentStepCode = step.step_code || currentStepCode;
    renderButtons(step.options || []);
  }

  function renderButtons(options) {
    buttons.innerHTML = "";
    options.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "btn btn-primary btn-choose btn-sm";
      button.textContent = option.label;
      button.addEventListener("click", () => choose(option));
      buttons.appendChild(button);
    });
  }

  function setTyping(visible) {
    typing.classList.toggle("d-none", !visible);
  }

  function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, Math.max(0, ms || 0)));
  }

  async function choose(option) {
    if (busy) return;
    busy = true;

    addMessage(true, option.label);
    buttons.innerHTML = "";
    setTyping(true);

    try {
      const data = await postJSON("/api/choose/", {
        step_code: currentStepCode,
        option_id: option.id === null || option.id === undefined ? null : option.id,
      });
      await wait(data.step ? data.step.delay_ms : 0);
      setTyping(false);
      handleResponse(data);
    } catch (error) {
      setTyping(false);
      addMessage(false, "⚠️ Кажется, связь с «дата-банком» прервалась. Попробуйте обновить страницу.");
    } finally {
      busy = false;
    }
  }

  function handleResponse(data) {
    if (!data || !data.ok) {
      addMessage(false, "⚠️ " + ((data && data.error) || "Неизвестная ошибка сервера."));
      return;
    }

    if (data.result === "end") {
      addMessage(false, data.text || "");
      buttons.innerHTML = "";
      return;
    }

    if (data.result === "restart") {
      chat.innerHTML = "";
      if (data.greeting) {
        addMessage(false, data.greeting.text);
        addImage(chat.lastChild.querySelector(".bubble"), data.greeting.image_url);
      }
      renderStep(data.step);
      return;
    }

    if (data.step) {
      renderStep(data.step);
    }
  }

  async function start() {
    busy = true;
    chat.innerHTML = "";
    buttons.innerHTML = "";
    setTyping(true);
    try {
      const data = await postJSON("/api/start/", {});
      await wait(data.step ? data.step.delay_ms : 0);
      setTyping(false);
      if (!data.ok) {
        addMessage(false, "⚠️ " + (data.error || "Сценарий не загружен."));
        return;
      }
      if (data.greeting) {
        addMessage(false, data.greeting.text);
        addImage(chat.lastChild.querySelector(".bubble"), data.greeting.image_url);
      }
      renderStep(data.step);
    } catch (error) {
      setTyping(false);
      addMessage(false, "⚠️ Не удалось начать диалог. Проверьте, что сервер запущен.");
    } finally {
      busy = false;
    }
  }

  document.getElementById("restart-top").addEventListener("click", async () => {
    if (busy) return;
    await start();
  });

  start();
})();
