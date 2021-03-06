
var Game = function(gameNo, word, id, counterId, listId, scoreId) {
    var gameNo = gameNo;
    var base = word;
    var $game = $(id);
    var $counter = $(counterId);
    var $list = $(listId);
    var $score = $(scoreId);
    var counter = 30;
    var words = [];
    var prevGuesses = {};
    var score = 0;
    var interval;
    $('#base').hide();
    for (var i = 0; i < base.length; i++) {
        $('#base' + i).html(base[i]);
    }

    var validate = function(guess, index) {
        $.get('/validate?guess=' + guess + '&base=' + base, function(data) {
            if (data.valid) {
                $('#word' + index).addClass('valid');
                score += guess.length;
                $score.html(score);
            }
            else {
                $('#word' + index).addClass('invalid');
            }
        });
    };

    return {
        start: function() {
            console.log("Starting the game...");
            $score.html(0);
            $counter.html(counter);
            $('#base').show();
            $game.show();
            var that = this;
            interval = setInterval(function() { that.updateCountdown(that); }, 1000);
        },
        updateCountdown: function(that) {
            counter -= 1;
            $counter.html(counter);
            if (counter <= 0) {
                that.finish(); 
                clearInterval(interval);
            }
        },
        finish: function() {
            $.post('/finish', {'score': score, 'gameID': gameNo}, function(data) {
                if (data.success) {
                    if (data.first) {
                        $('#modehead').html('Nice work!');
                        $('#modebody').html('We\'re waiting for an opponent to finsh this game.');
                    } else if (data.win) {
                        $('#modehead').html('Congratulations!');
                        $('#modebody').html('You won! Way to go.');
                    } else {
                        $('#modehead').html('Nice try!');
                        $('#modebody').html('You lost this time. Try again!');
                    }
                    $('#over').modal('show');
                    console.log('callback from /endgame');
                    console.log(score);
                } 
            })         
        },
        guess: function(theGuess) {
            if (prevGuesses[theGuess] != undefined) {
                return; 
            }
            words.push(theGuess);
            prevGuesses[theGuess] = true;
            var i = words.length - 1;
            $list.prepend('<div class="row"> <div class="span1 offset1" id=word' + i + '>' + theGuess + '</div></div>');
            validate(theGuess, i);
        }
    }; 
}

