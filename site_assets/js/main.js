const messagesContainer = document.getElementById("messages");
const messageTemplate = document.getElementById("message-template");
const messagesController = {
    addMessage: (message, type = "info") => {
        if (!messagesContainer || !messageTemplate) return;
        console.log(messageTemplate);
        const clone = messageTemplate.cloneNode(true);
        clone.id = "";
        clone.classList.remove("d-none");
        clone.classList.add(`alert-${type}`);
        clone.insertBefore(document.createTextNode(message), clone.querySelector(".btn-close"));
        messagesContainer.appendChild(clone);
    }
}
