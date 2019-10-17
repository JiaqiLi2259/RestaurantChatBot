// Please replace the YOUR_API_ENDPOINT_URL in line 3 with yours
// Please replace the apiKey in line 5 and line 18 with yours
let API_ENDPOINT = 'YOUR API GATEWAY ENDPOINT';
let apigClient = apigClientFactory.newClient({
    apiKey : 'YOUR API KEY'
});
let messagesArray = [];
let monthsInEng = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

// Setup divs that will be used to display interactive messages
var errorDiv = document.getElementById('error-message');
var successDiv = document.getElementById('success-message');
var resultsDiv = document.getElementById('results-message');
var container = document.getElementById("msgs_div");
var headerParams = {
    //This is where any header, path, or querystring request params go. The key is the parameter named as defined in the API
    "Content-type": "application/json",
    "x-api-key": "YOUR API KEY",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials" : "true", 
    "Access-Control-Allow-Methods" : "GET,HEAD,OPTIONS,POST,PUT",
    "Access-Control-Allow-Headers" : "Access-Control-Allow-Headers, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
};

// Add listeners for each button that make the API request
document.getElementById('sendButton').addEventListener('click', function(e) {
    sendChatInputToApi(e);
});

// Listen to the Enter key in keyboard
$(document).keydown(function(event){
    if(event.keyCode == 13){
        $("#sendButton").click();
    }
});

// Setup easy way to reference values of the input boxes
function messageValue() { return document.getElementById('message').value }

// Clear any exisiting notifications in the browser notifications divs
function clearNotifications() {
    errorDiv.textContent = '';
    resultsDiv.textContent = '';
    successDiv.textContent = '';
}

// Prepare to send data to AWS Gateway
function sendChatInputToApi(e){
    e.preventDefault()
    clearNotifications()
    let inputQuery = messageValue();
    callChatApi({ "message": inputQuery });
    let chatInputBox = document.getElementById("message");
    chatInputBox.value = "";
    chatInputBox.textContent = '';
}

// Send HTTP POST request to AWS Gateway
function callChatApi(query) {
    apigClient.chatbotPost(headerParams, query, {})
        .then(function(result) {
            console.log(result);
            let msg = { "query" : query.message, "response" : result.data }
            messagesArray.push(msg)
            render();
            //resultsDiv.textContent = JSON.stringify(result.data);
        })
        .catch(function(err) {
            errorDiv.textContent = 'Failed! There was an error:\n' + err.toString();
        });
}           

// Refresh HTML with new messages
function render(){
    //container.innerHTML = "";
    for (var i = 0; i < messagesArray.length; i++) {
        var myDate = new Date();
        var month = monthsInEng[myDate.getMonth()];
        var day = myDate.getDate();
        var hour = myDate.getHours();
        var minute = myDate.getMinutes();
        let perMessage = messagesArray[i];
        container.innerHTML += `
        <div>
            <div class="outgoing_msg">
                <div class="sent_msg">
                <p>` + perMessage.query + `</p>
                <span class="time_date">` + hour + `:` + minute + `    |    ` + month + ` ` + day + `</span>
                </div>
            </div>
            <div class="incoming_msg">
                <div class="incoming_msg_img"> <img src="https://ptetutorials.com/images/user-profile.png" alt="sunil">
                </div>
                <div class="received_msg">
                <div class="received_withd_msg">
                    <p> ` + perMessage.response + `</p>
                    <span class="time_date">` + hour + `:` + minute + `    |    ` + month + ` ` + day + `</span>                   
                </div>
                </div>
            </div>
        </div>`;
        container.scrollTop = container.scrollHeight;
        messagesArray = [];
    }
}
