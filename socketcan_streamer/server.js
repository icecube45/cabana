const CanMessage = require('can-message');
const WebSocket = require('ws')
const MAX_MESSAGE_QUEUE = 100;

var can = require('socketcan');

const wss = new WebSocket.Server({ port: 8080 })

var channel = can.createRawChannel("can0", true);
var client;
var count = 0;

var can_packet = new Buffer(0)
channel.addListener("onMessage", function(msg) { 
  console.log(msg);
  can_packet = Buffer.concat([can_packet, CanMessage.packCAN({
    address: msg.id,
    data: msg.data,
    bus: 0
    })]);

count = count+1;

if(count === MAX_MESSAGE_QUEUE){
  count = 0;
  client.send(can_packet); 
  can_packet = new Buffer(0);
  console.log("sent");
}

timeoutId.refresh();

} );

const timeoutId = setTimeout(() => {
  if(count!=0){
    count=0;
    console.log(can_packet);

    client.send(can_packet); 
    can_packet = new Buffer(0);
  }
  console.log("timeout, send remaining data")
}, 0.5 * 1000);  timeoutId.unref();
  
wss.on('connection', ws => {
  console.log('connection!');
  client = ws;
});
//   ws.on('message', message => {
//     console.log(`Received message => ${message}`)
//   })
//   ws.send('ho!')
// })

channel.start();
