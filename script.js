var inputBox = document.getElementById("message");
		var output = document.getElementById("output");
		var connect = document.getElementById("init");
		var form = document.getElementById("form");

var gameSign = null;

// Event for cell
var cell = document.getElementsByClassName('cell');
for (var i = 0; i < cell.length; i++) {
	cell[i].addEventListener('click', function(e){
		if (!e.target.classList.contains('check')) {
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
		}
	}, false);
}


// Active servers
var hosts = ["ws://localhost:9876/test", "ws://localhost:9872/test", "ws://localhost:9877/test"]

// Web Socket object
var socket = null;

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
			if (data[i] == "'0'") {
				cell[i].style.backgroundImage = 'url(pic/cross.png)';
				cell[i].style.backgroundSize = 'cover';
			} else {
				cell[i].style.backgroundImage = 'url(pic/circle.png)';
				cell[i].style.backgroundSize = 'cover';
			}
		}
	}
	return data
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
			var p = document.createElement("p");
			if (e.data == 1 || e.data == 0) {
				gameSign = e.data;
			}
			else {
				var arr = e.data;
				arr = otherPlayerStep(arr);
			}
			p.innerHTML = e.data;
			output.appendChild(p);
		};
				
	} catch (ex) {
		console.log("Socket exception:", ex);
		s.close()
		s = null;
	}

	return s;
}

// Create Web Socket object
var socket = init(hosts[0]);

		/*connect.addEventListener("click", function () {
			socket = init(hosts[0]);
			}, false)*/
form.addEventListener("submit", function (e) {
	e.preventDefault();
	socket.send(inputBox.value);
	inputBox.value = "";
}, false)