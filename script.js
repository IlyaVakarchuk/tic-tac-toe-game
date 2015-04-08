var gameSign = null;

// 0 - Progress is blocked. Another player to make a move
// 1 - Player must move. Another player is waiting
var gameState = 0;

// Secondary servers
var hosts = ["ws://localhost:9876/test", "ws://localhost:9872/test", "ws://localhost:9877/test"]

// Web Socket object
var socket = null;

// DOM's elements
var cell = null;
var stat = document.getElementById('statistic');
var step = document.getElementById('step');
var login = document.getElementById('login');

// Connect to server, after player pressed 'CONNECT' button
connect.addEventListener('click', function() { 
	socket = init(hosts[0]);
	var connect = document.getElementById('connect');
	var name = document.getElementById('name');
	name.disabled = 0;
	name.style.opacity = '1';
	login.disabled = 0;
	login.style.opacity = '1';
	// Login on server. 
	login.addEventListener('click', function(){
	 	var name = document.getElementById('name');
	 	socket.send(name.value);
	 	var wait = document.getElementById('wait-indicator');
	 	wait.style.display = 'block';
	 	connect.disabled = 1;
	 	name.disabled = 1;
	 	login.disabled = 1;
	 	connect.style.opacity = '0.2';
	 	name.style.opacity = '0.2';
	 	login.style.opacity = '0.2';
	 },false)
} ,false)

// Event for cell
function addEvents() {
	cell = document.getElementsByClassName('cell');
	for (var i = 0; i < cell.length; i++) {
		cell[i].addEventListener('click', function(e){
			// If cell is empty and players can move
			if (!e.target.classList.contains('check') && gameState == 1) {
				var possition = e.target.getAttribute('data-item');
				e.target.classList.add('check');
				if (gameSign == 0) {
					e.target.style.backgroundImage = 'url(pic/cross.png)';
					e.target.style.backgroundSize = 'cover';
				} else if (gameSign == 1) {
					e.target.style.backgroundImage = 'url(pic/circle.png)';
					e.target.style.backgroundSize = 'cover';
				}
				socket.send(possition + ' ' + gameSign);
				gameState = 0;
				stat.style.backgroundColor = '#e57272';
				step.innerHTML = 'Second player step';
			}
		}, false);
	}
}

// Show game board
function gameBegin() {
	var wait = document.getElementById('wait-indicator');
	wait.style.display = 'none';
	var table = document.getElementById('table');
	table.style.display = 'inline-block'
	addEvents();
	stat.style.display = 'inline-block';
}

// Change board. 
function otherPlayerStep(data){
	data = data.replace('[[', '');
	data = data.replace(',', '');
	data = data.replace('[', '');
	data = data.replace('[', '');
	data = data.replace(']', '');
	data = data.replace(']', '');
	data = data.replace(']]', '');

	for (var i = 0 ; i < 8; i++) {
		data = data.replace(',', '');	
	}
	data = data.split(' ');
	for (var i = 0; i < data.length; i++) {
		if (data[i] == "'0'" || data[i] == "'1'") {
			cell[i].classList.add('check');
			// CROSS select
			if (data[i] == "'0'") {
				cell[i].style.backgroundImage = 'url(pic/cross.png)';
				cell[i].style.backgroundSize = 'cover';
			// TOE select
			} else {
				cell[i].style.backgroundImage = 'url(pic/circle.png)';
				cell[i].style.backgroundSize = 'cover';
			}
		}
	}
	return data
}

// Show result of the game
function gameOver(result) {
	var board = document.getElementById('board');
	var table = document.getElementById('table');
	table.style.display = 'none';
	stat.style.display = 'none';

	// WIN case
	if (result == 'GAME OVER! You WIN!') {
		board.style.backgroundColor = '#aaeeb9';
		board.style.backgroundImage = 'url(pic/win.png)';
		board.style.backgroundSize = 'cover';
	// LOSE case
	} else if (result == 'GAME OVER! You LOSE!') {
		board.style.backgroundColor = '#e57272';
		board.style.backgroundImage = 'url(pic/lose.png)';
		board.style.backgroundSize = 'cover';
	// STANDOFF case
	} else if (result == 'GAME OVER! STANDOFF!') {
		board.style.backgroundColor = '#c3c3c3';
		board.style.backgroundImage = 'url(pic/standoff.png)';
		board.style.backgroundSize = 'cover';
	}
}

// Open new socket
function init(host) {
			
	// WebSocket object
	var s = null;

	// Create WebSocket object
	try {
		console.log("Host:", host);
				
		s = new WebSocket(host);

		s.onopen = function (e) {
			console.log("Socket opened.");
		};

		s.onclose = function (e) {
			s.close();
			console.log("Socket closed.");
			var index = (Math.floor(Math.random() * (hosts.length - 0) + 0));
			socket = init(hosts[index]);
		}

		s.onerror = function (e) {
			console.log("Socket exception:", e);
		};

		s.onmessage = function (e) {
			console.log("Socket message:", e.data);
			if (e.data == 1 || e.data == 0) {
				gameSign = e.data;
				if (gameSign == 0) {
					gameState = 1
					stat.style.backgroundColor = '#aaeeb9';
					step.innerHTML = 'You step';
				}
				gameBegin();
			}
			else if (e.data == 'GAME OVER! You WIN!' || e.data == 'GAME OVER! You LOSE!' || e.data == 'GAME OVER! STANDOFF!') {
				gameOver(e.data);
			}
			else if (e.data == 'STEP?') {
				socket.send(gameState);
			}
			else {
				var arr = e.data;
				arr = otherPlayerStep(arr);
				gameState = 1;
				stat.style.backgroundColor = '#aaeeb9';
				step.innerHTML = 'You step';
			}
		};
				
	} catch (ex) {
		console.log("Socket exception:", ex);
		s.close()
		s = null;
	}

	return s;
}