
var Game = function(gameNo, word, id, counterId, listId, scoreId) {
    var gameNo = gameNo;
    var base = word;
    var $game = $(id);
    var $counter = $(counterId);
    var $list = $(listId);
    var $score = $(scoreId);
    var counter = 60;
    var words = [];
    var prevGuesses = {};
    var score = 0;
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
            $counter.html(60);
            $('#base').show();
            $game.show();
            setTimeout(this.updateCountdown, 1000);
        },
        updateCountdown: function() {
            counter -= 1;
            $counter.html(counter);
            if (counter <= 0) {
                this.finish(); 
            }
            else {
                setTimeout(this.updateCountdown, 1000);
            }
        },
        finish: function() {
            $.post('/finish', {'score': score, 'game': gameNo}, function(data) {
                if (data.success) {
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
            $list.prepend('<li id=word' + i + '>' + theGuess + '</li>');
            validate(theGuess, i);
        }
    }; 
}

