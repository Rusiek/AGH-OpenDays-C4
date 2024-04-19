// script.js
document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start-game');
    const newGameButton = document.getElementById('new-game');
    const boardElement = document.getElementById('board');
    const cellsContainer = document.getElementById('board-cells');
    const dropZone = document.getElementById('drop-zone');
    const probabilities = document.getElementById('probabilities');
    const model = document.getElementById('ai-model');

    const dropCells = document.querySelectorAll('.drop-cell');
    dropCells.forEach(cell => {
        cell.addEventListener('mouseenter', () => {
            cell.style.backgroundColor = '#dfc639'; // Zmiana koloru tła przy najechaniu
        });
        cell.addEventListener('mouseleave', () => {
            cell.style.backgroundColor = '#ccc'; // Przywrócenie oryginalnego koloru tła
        });
    });


    let selectedModel = 'random'; // Default model
    let gameActive = false;

    model.addEventListener('change', (event) => {
        selectedModel = event.target.value;
        console.log(`Selected model: ${selectedModel}`);
    });

    // Create probability indicators and drop cells
    for (let i = 0; i < 7; i++) {
        let probValue = document.createElement('div');
        probValue.className = 'probability-value';
        probValue.textContent = '0%'; // Default value
        probabilities.appendChild(probValue);

        let dropCell = document.createElement('div');
        dropCell.className = 'drop-cell';
        dropCell.addEventListener('click', () => makeMove(i));
        dropZone.appendChild(dropCell);
    }

    startButton.addEventListener('click', startGame);
    newGameButton.addEventListener('click', newGame);

    function initializeBoard() {
        const cellsContainer = document.getElementById('board-cells');
        for (let i = 0; i < 42; i++) { // 7 kolumn x 6 rzędów
            let cell = document.createElement('div');
            cell.className = 'cell';
            cellsContainer.appendChild(cell);
        }
    }

    function startGame() {
        startButton.style.display = 'none';
        newGameButton.style.display = 'block';
        boardElement.style.display = 'block';
        board = Array(7).fill(0).map(() => Array(6).fill(0));
        Array.from(cellsContainer.children).forEach(cell => cell.style.backgroundColor = 'white');
        // Initialize game logic, including fetching initial probabilities
        updateProbabilities([
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1)
        ]); // Values rounded to one decimal place
        initializeBoard();
    }
    

    function newGame() {
        console.log("New Game Started");
        gameActive = true;
        board = Array(7).fill(0).map(() => Array(6).fill(0));
        Array.from(cellsContainer.children).forEach(cell => cell.style.backgroundColor = 'white');
        updateProbabilities([
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1),
            (100 * 1 / 7).toFixed(1)
        ]);
    }

    function handleEndGame(winner) {
        setTimeout(() => {
            if (winner === 1) {
                console.log("Gratulacje! Wygrałeś!");
                alert("Gratulacje! Wygrałeś!");
                newGame();
                return true;
            } 
            else if (winner === 2) {
                console.log("AI wygrywa ;-;");
                alert("AI wygrywa ;-;");
                newGame();
                return true;
            } 
            else if (winner === 'draw') {
                console.log("Remis!");
                alert("Remis!");
                newGame();
                return true;
            }
        }, 1000);
        return false;
    }

    function makeMove(column) {
        if (!gameActive) {
            console.log("Game is over. No more moves allowed.");
            return;
        }
        console.log(`Player move made in column ${column}`);
        updateBoard(column, 1);
        let winner = checkForWinner(board);
        if (winner) {
            handleEndGame(winner);
            return;
        }
        gameActive = false;
        fetchMoveFromServer();
    }

    function checkForWinner(board) {
        const rows = board[0].length;
        const cols = board.length;
    
        // Sprawdzanie poziome
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols - 3; c++) {
                if (board[c][r] !== 0 && board[c][r] === board[c + 1][r] && board[c][r] === board[c + 2][r] && board[c][r] === board[c + 3][r]) {
                    return board[c][r]; // Zwraca zwycięzcy
                }
            }
        }
    
        // Sprawdzanie pionowe
        for (let c = 0; c < cols; c++) {
            for (let r = 0; r < rows - 3; r++) {
                if (board[c][r] !== 0 && board[c][r] === board[c][r + 1] && board[c][r] === board[c][r + 2] && board[c][r] === board[c][r + 3]) {
                    return board[c][r]; // Zwraca zwycięzcy
                }
            }
        }
    
        // Sprawdzanie przekątnych (w dół i w prawo)
        for (let r = 0; r < rows - 3; r++) {
            for (let c = 0; c < cols - 3; c++) {
                if (board[c][r] !== 0 && board[c][r] === board[c + 1][r + 1] && board[c][r] === board[c + 2][r + 2] && board[c][r] === board[c + 3][r + 3]) {
                    return board[c][r];
                }
            }
        }
    
        // Sprawdzanie przekątnych (w dół i w lewo)
        for (let r = 3; r < rows; r++) {
            for (let c = 0; c < cols - 3; c++) {
                if (board[c][r] !== 0 && board[c][r] === board[c + 1][r - 1] && board[c][r] === board[c + 2][r - 2] && board[c][r] === board[c + 3][r - 3]) {
                    return board[c][r];
                }
            }
        }
    
        // Sprawdzenie remisu
        if (board.every(column => column.every(cell => cell !== 0))) {
            return 'draw'; // Zwraca remis, jeśli wszystkie komórki są zajęte
        }
    
        return null; // Brak zwycięzcy ani remisu
    }
    
    function updateBoard(column, player) {
        // Sprawdzamy od dołu każdej kolumny, aby znaleźć pierwsze puste miejsce (0 oznacza puste)
        for (let row = board[column].length - 1; row >= 0; row--) {
            if (board[column][row] === 0) {
                board[column][row] = player; // Ustawiamy gracz lub AI (1 lub 2)
                updateCell(column, row, player);
                return;
            }
        }
        console.log("Column is full or invalid input."); // Logujemy, jeśli kolumna jest pełna
        alert("Kolumna jest pełna, wybierz inną.");
    }

    function updateCell(column, row, player) {
        const index = row * 7 + column;
        const cell = cellsContainer.children[index];
        cell.style.backgroundColor = player === 1 ? 'red' : 'yellow'; // Gracz 1 to czerwony, gracz 2 to żółty
    }
    
    function fetchMoveFromServer() {
        const aiMode = document.getElementById('ai-model').value;

        const urlMap = {
            random: 'http://localhost:5000/move_random',
            random_smart_1: 'http://localhost:5000/move_minmax',
            random_smart_2: 'http://localhost:5000/move_minmax',
            random_smart_3: 'http://localhost:5000/move_minmax',
            random_smart_4: 'http://localhost:5000/move_minmax',
            minmax_cache: 'http://localhost:5000/move_minmax_cache',
            mcts_1: 'http://localhost:5000/move_monte_carlo',
            mcts_2: 'http://localhost:5000/move_monte_carlo',
            mcts_3: 'http://localhost:5000/move_monte_carlo',
            mcts_4: 'http://localhost:5000/move_monte_carlo',
            mcts_5: 'http://localhost:5000/move_monte_carlo',
            mcts_6: 'http://localhost:5000/move_monte_carlo'
        };

        const url = urlMap[aiMode] || urlMap.random;

        if (aiMode === 'random_smart_1') {
            console.log("random_smart_1");
            body = JSON.stringify({board: board, power: 2});
        }
        else if (aiMode === 'random_smart_2') {
            console.log("random_smart_2");
            body = JSON.stringify({board: board, power: 3});
        }
        else if (aiMode === 'random_smart_3') {
            console.log("random_smart_3");
            body = JSON.stringify({board: board, power: 5});
        }
        else if (aiMode === 'random_smart_4') {
            console.log("random_smart_4");
            body = JSON.stringify({board: board, power: 7});
        }
        else if (aiMode === 'minmax_cache') {
            console.log("minmax_cache");
            body = JSON.stringify({board: board, power: 6});
        }
        else if (aiMode === 'mcts_1') {
            console.log("mcts_1");
            body = JSON.stringify({board: board, power: 1000});
        }
        else if (aiMode === 'mcts_2') {
            console.log("mcts_2");
            body = JSON.stringify({board: board, power: 10000});
        }
        else if (aiMode === 'mcts_3') {
            console.log("mcts_3");
            body = JSON.stringify({board: board, power: 100000});
        }
        else if (aiMode === 'mcts_4') {
            console.log("mcts_4");
            body = JSON.stringify({board: board, runtime: 1});
        }
        else if (aiMode === 'mcts_5') {
            console.log("mcts_5");
            body = JSON.stringify({board: board, runtime: 3});
        }
        else if (aiMode === 'mcts_6') {
            console.log("mcts_6");
            body = JSON.stringify({board: board, runtime: 10});
        }
        else {
            body = JSON.stringify({board: board});
        }

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: body
        })
        .then(response => response.json())
        .then(data => {
            console.log(`AI move made in column ${data.column}`);
            if (data.column >= 0) {
                updateBoard(data.column, 2); // Assume 2 represents AI's move
                highLightDropCell(data.column);
                updateProbabilities(data.probabilities);
                let winner = checkForWinner(board);
                if (winner) {
                    handleEndGame(winner);
                }
                gameActive = true;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            gameActive = false;
        });
    }

    function highLightDropCell(column) {
        const dropCells = document.querySelectorAll('.drop-cell');
        const cell = dropCells[column];
        cell.classList.add('highlight');
        setTimeout(() => cell.classList.remove('highlight'), 500);
    }

    function updateProbabilities(values) {
        Array.from(probabilities.children).forEach((elem, index) => {
            elem.textContent = `${values[index]}%`;
        });
    }
    
});
