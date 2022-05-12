'use strict';

// mainpart taken from internet

var tinderContainer = document.querySelector('.tinder');
var allCards = document.querySelectorAll('.tinder--card');
var nope = document.getElementById('nope');
var love = document.getElementById('love');

// our variables we take to fetch users decissions

var returns = []
var ret_len = 0
var u_js = {}

//creates the cards, that can be shuffeld

function initCards(card, index) {
  var newCards = document.querySelectorAll('.tinder--card:not(.removed)');

  newCards.forEach(function (card, index) {
    card.style.zIndex = allCards.length - index;
    card.style.transform = 'scale(' + (20 - index) / 20 + ') translateY(-' + 30 * index + 'px)';
    card.style.opacity = (10 - index) / 10;
  });
  
  tinderContainer.classList.add('loaded');

  //checking if cards are left (self coded)

  if (newCards.length == 0) {
    //console.log("hier")
    //console.log(ret_len)
    
    // getting the usecase (new acc or weekly swipe)

    if (returns.length == 10) {

      // badly coded, but changing the list to a json that can be send via post

      u_js.one_id = returns[0][0]
      u_js.one_we = returns[0][1]

      u_js.two_id = returns[1][0]
      u_js.two_we = returns[2][1]

      u_js.three_id = returns[2][0]
      u_js.three_we = returns[2][1]

      u_js.four_id = returns[3][0]
      u_js.four_we = returns[3][1]

      u_js.five_id = returns[4][0]
      u_js.five_we = returns[4][1]

      u_js.six_id = returns[5][0]
      u_js.six_we = returns[5][1]

      u_js.seven_id = returns[6][0]
      u_js.seven_we = returns[6][1]

      u_js.eight_id = returns[7][0]
      u_js.eight_we = returns[7][1]

      u_js.nine_id = returns[8][0]
      u_js.nine_we = returns[8][1]

      u_js.ten_id = returns[9][0]
      u_js.ten_we = returns[9][1]


      var show = JSON.stringify(u_js)

      //creating post request

      let xhr = new XMLHttpRequest();

      //posting to addratings, which converts decissions into db entries

      xhr.open("POST", "/addratings");
      
      xhr.setRequestHeader("Accept", "application/json");
      xhr.setRequestHeader("Content-Type", "application/json");
      
      xhr.onload = () => console.log(xhr.responseText);
      
      let data = show;
      
      xhr.send(data);

      //redirecting the user
      
      window.location="/weekplan"

      console.log("10")
    }
    
    // same for weekly swipe

    if (returns.length == 5) {

      u_js.one_id = returns[0][0]
      u_js.one_we = returns[0][1]

      u_js.two_id = returns[1][0]
      u_js.two_we = returns[2][1]

      u_js.three_id = returns[2][0]
      u_js.three_we = returns[2][1]

      u_js.four_id = returns[3][0]
      u_js.four_we = returns[3][1]

      u_js.five_id = returns[4][0]
      u_js.five_we = returns[4][1]

      var show = JSON.stringify(u_js)


      let xhr = new XMLHttpRequest();

      xhr.open("POST", "/addratings");
      
      xhr.setRequestHeader("Accept", "application/json");
      xhr.setRequestHeader("Content-Type", "application/json");
      
      xhr.onload = () => console.log(xhr.responseText);
      
      let data = show;
      
      xhr.send(data);
      
      window.location="/weekplan"

      console.log("5")
    }
  }

}


initCards();

//enables the motion control

allCards.forEach(function (el) {
  var hammertime = new Hammer(el);

  hammertime.on('pan', function (event) {
    el.classList.add('moving');
  });

  hammertime.on('pan', function (event) {
    if (event.deltaX === 0) return;
    if (event.center.x === 0 && event.center.y === 0) return;

    tinderContainer.classList.toggle('tinder_love', event.deltaX > 0);
    tinderContainer.classList.toggle('tinder_nope', event.deltaX < 0);

    var xMulti = event.deltaX * 0.03;
    var yMulti = event.deltaY / 80;
    var rotate = xMulti * yMulti;

    event.target.style.transform = 'translate(' + event.deltaX + 'px, ' + event.deltaY + 'px) rotate(' + rotate + 'deg)';
  });

  hammertime.on('panend', function (event) {
    el.classList.remove('moving');
    tinderContainer.classList.remove('tinder_love');
    tinderContainer.classList.remove('tinder_nope');

    var moveOutWidth = document.body.clientWidth;
    var keep = Math.abs(event.deltaX) < 80 || Math.abs(event.velocityX) < 0.5;

    event.target.classList.toggle('removed', !keep);

    if (keep) {
      event.target.style.transform = '';
    } else {
      var endX = Math.max(Math.abs(event.velocityX) * moveOutWidth, moveOutWidth);
      var toX = event.deltaX > 0 ? endX : -endX;
      var endY = Math.abs(event.velocityY) * moveOutWidth;
      var toY = event.deltaY > 0 ? endY : -endY;
      var xMulti = event.deltaX * 0.03;
      var yMulti = event.deltaY / 80;
      var rotate = xMulti * yMulti;

      var card_id = el.id

      //our code, checking which direction is swiped
      //tox gives direction

      var ret = []

      //all adding the card id, which equals the dish id and the decission

      if (toX > 0 ) {
        console.log("like")
        ret[0] = card_id
        ret[1] = 1

        console.log(card_id)


        returns[ret_len] = ret

        ret_len = ret_len + 1
      }
      if (toX < 0 ) {
        console.log("dont")
        ret[0] = card_id
        ret[1] = 0

        console.log(card_id)

        returns[ret_len] = ret
        ret_len = ret_len + 1
      }

      event.target.style.transform = 'translate(' + toX + 'px, ' + (toY + event.deltaY) + 'px) rotate(' + rotate + 'deg)';
      initCards();
    }
  });
});

//user can also decide with buttons

function createButtonListener(love) {
  return function (event) {
    var cards = document.querySelectorAll('.tinder--card:not(.removed)');
    var moveOutWidth = document.body.clientWidth * 1.5;

    if (!cards.length) return false;

    var card = cards[0];

    card.classList.add('removed');

    var card_id = card.id

    var ret = []

    //our code, same as above

    if (love) {
      card.style.transform = 'translate(' + moveOutWidth + 'px, -100px) rotate(-30deg)';

      ret[0] = card_id
      ret[1] = 1
      console.log(card_id)
      returns[ret_len] = ret
      ret_len = ret_len + 1

    } else {
      card.style.transform = 'translate(-' + moveOutWidth + 'px, -100px) rotate(30deg)';

      ret[0] = card_id
      ret[1] = 0

      console.log(card_id)

      returns[ret_len] = ret
      ret_len = ret_len + 1
    }

    initCards();

    event.preventDefault();
  };
}

var nopeListener = createButtonListener(false);
var loveListener = createButtonListener(true);

nope.addEventListener('click', nopeListener);
love.addEventListener('click', loveListener);