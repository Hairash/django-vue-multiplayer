const socket = new WebSocket("ws://localhost:8000/ws/game/");

socket.addEventListener("open", (event) => {
  // The WebSocket connection is now open, and you can safely send data
  // For example:
  // socket.send(JSON.stringify({ action: "join", username: "player1" }));
  sendMove();
});

socket.addEventListener("message", (event) => {
  // const data = JSON.parse(event.data);
  console.log(event.data);
  // Update the game state in your Vue component based on the received data
});

// Wrap the send action in a function
function sendMove() {
  if (socket.readyState === WebSocket.OPEN) {
    // socket.send(JSON.stringify({ action: "move" }));
    socket.send('0');
  } else {
    console.error("WebSocket is not open. readyState:", socket.readyState);
  }
}
