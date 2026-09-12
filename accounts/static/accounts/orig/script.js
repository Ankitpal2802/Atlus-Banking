function getCsrfToken() {
    var input = document.querySelector('#transferForm input[name="csrfmiddlewaretoken"]');
    return input ? input.value : "";
}

function transfer() {
    var toAccount = document.getElementById("toAccount").value;
    var amount = document.getElementById("amount").value;
    var messageEl = document.getElementById("message");

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/transfer/submit/", true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            var text = xhr.status === 200 ? xhr.responseText : (xhr.responseText || ("Error: " + xhr.status));
            messageEl.innerHTML = text;
            messageEl.classList.remove("success", "error");
            messageEl.classList.add(xhr.status === 200 ? "success" : "error");
            if (xhr.status === 200) {
                document.getElementById("transferForm").reset();
            }
        }
    };
    xhr.send("toAccount=" + encodeURIComponent(toAccount) + "&amount=" + encodeURIComponent(amount));
}
