import streamlit as st
import numpy as np
import random
import time

BOARD_SIZE = 4

# --- Game logic functions ---

def new_board():
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    add_random_tile(board)
    add_random_tile(board)
    return board


def add_random_tile(board):
    empties = list(zip(*np.where(board == 0)))
    if not empties:
        return False
    r, c = random.choice(empties)
    board[r, c] = 4 if random.random() < 0.1 else 2
    return True


def compress(row):
    """Slide non-zero elements to the left (remove zeros)."""
    new_row = [num for num in row if num != 0]
    new_row += [0] * (len(row) - len(new_row))
    return new_row


def merge(row):
    """Merge a row after compression. Returns new row and gained score."""
    score = 0
    for i in range(len(row) - 1):
        if row[i] != 0 and row[i] == row[i + 1]:
            row[i] *= 2
            row[i + 1] = 0
            score += row[i]
    return row, score


def move_left(board):
    moved = False
    score_gain = 0
    new_board = np.zeros_like(board)
    for i in range(BOARD_SIZE):
        row = list(board[i])
        compressed = compress(row)
        merged, gained = merge(compressed)
        final = compress(merged)
        new_board[i] = final
        if not np.array_equal(new_board[i], board[i]):
            moved = True
        score_gain += gained
    return new_board, moved, score_gain


def move_right(board):
    reversed_board = np.fliplr(board)
    moved_board, moved, score_gain = move_left(reversed_board)
    return np.fliplr(moved_board), moved, score_gain


def move_up(board):
    transposed = board.T
    moved_board, moved, score_gain = move_left(transposed)
    return moved_board.T, moved, score_gain


def move_down(board):
    transposed = board.T
    moved_board, moved, score_gain = move_right(transposed)
    return moved_board.T, moved, score_gain


def can_move(board):
    if np.any(board == 0):
        return True
    # check horizontal
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE - 1):
            if board[i, j] == board[i, j + 1]:
                return True
    # check vertical
    for j in range(BOARD_SIZE):
        for i in range(BOARD_SIZE - 1):
            if board[i, j] == board[i + 1, j]:
                return True
    return False


# --- Rendering helpers ---

TILE_COLORS = {
    0: ("#cdc1b4", "#776e65"),
}
# Enhanced color palette with gradients
base_colors = [
    ("linear-gradient(135deg, #eee4da, #ede0c8)", "#776e65"),  # 2
    ("linear-gradient(135deg, #ede0c8, #f2b179)", "#776e65"),  # 4
    ("linear-gradient(135deg, #f2b179, #f59563)", "#f9f6f2"),  # 8
    ("linear-gradient(135deg, #f59563, #f67c5f)", "#f9f6f2"),  # 16
    ("linear-gradient(135deg, #f67c5f, #f65e3b)", "#f9f6f2"),  # 32
    ("linear-gradient(135deg, #f65e3b, #edcf72)", "#f9f6f2"),  # 64
    ("linear-gradient(135deg, #edcf72, #edcc61)", "#f9f6f2"),  # 128
    ("linear-gradient(135deg, #edcc61, #edc850)", "#f9f6f2"),  # 256
    ("linear-gradient(135deg, #edc850, #edc53f)", "#f9f6f2"),  # 512
    ("linear-gradient(135deg, #edc53f, #edc22e)", "#f9f6f2"),  # 1024
    ("linear-gradient(135deg, #edc22e, #ff6b35)", "#f9f6f2"),  # 2048
    ("linear-gradient(135deg, #ff6b35, #f7931e)", "#f9f6f2"),  # 4096
    ("linear-gradient(135deg, #f7931e, #ffcc02)", "#f9f6f2"),  # 8192
]
for i, col in enumerate(base_colors, start=1):
    TILE_COLORS[2 ** i] = col


def get_css_styles():
    return """
    <style>
    @keyframes tileAppear {
        0% { transform: scale(0.8); opacity: 0; }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    @keyframes tileMerge {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    
    @keyframes tileMove {
        0% { transform: translateX(0) translateY(0); }
        100% { transform: translateX(var(--target-x)) translateY(var(--target-y)); }
    }
    
    @keyframes scorePopup {
        0% { transform: translateY(0) scale(1); opacity: 1; }
        100% { transform: translateY(-50px) scale(1.5); opacity: 0; }
    }
    
    @keyframes boardShake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-2px); }
        75% { transform: translateX(2px); }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(255, 255, 255, 0.5); }
        50% { box-shadow: 0 0 20px rgba(255, 255, 255, 0.8), 0 0 30px rgba(255, 255, 255, 0.6); }
    }
    
    .game-board {
        background: linear-gradient(135deg, #bbada0, #cdc1b4);
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .game-board::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        animation: shimmer 3s infinite;
        pointer-events: none;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .board-row {
        display: flex;
        gap: 12px;
        margin-bottom: 12px;
    }
    
    .tile {
        width: 90px;
        height: 90px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        border-radius: 8px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .tile::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s ease;
    }
    
    .tile:hover::before {
        left: 100%;
    }
    
    .tile-2 { background: linear-gradient(135deg, #eee4da, #ede0c8); color: #776e65; font-size: 32px; }
    .tile-4 { background: linear-gradient(135deg, #ede0c8, #f2b179); color: #776e65; font-size: 32px; }
    .tile-8 { background: linear-gradient(135deg, #f2b179, #f59563); color: #f9f6f2; font-size: 32px; }
    .tile-16 { background: linear-gradient(135deg, #f59563, #f67c5f); color: #f9f6f2; font-size: 28px; }
    .tile-32 { background: linear-gradient(135deg, #f67c5f, #f65e3b); color: #f9f6f2; font-size: 28px; }
    .tile-64 { background: linear-gradient(135deg, #f65e3b, #edcf72); color: #f9f6f2; font-size: 28px; }
    .tile-128 { background: linear-gradient(135deg, #edcf72, #edcc61); color: #f9f6f2; font-size: 24px; }
    .tile-256 { background: linear-gradient(135deg, #edcc61, #edc850); color: #f9f6f2; font-size: 24px; }
    .tile-512 { background: linear-gradient(135deg, #edc850, #edc53f); color: #f9f6f2; font-size: 24px; }
    .tile-1024 { background: linear-gradient(135deg, #edc53f, #edc22e); color: #f9f6f2; font-size: 20px; }
    .tile-2048 { background: linear-gradient(135deg, #edc22e, #ff6b35); color: #f9f6f2; font-size: 20px; animation: glow 2s infinite; }
    .tile-4096 { background: linear-gradient(135deg, #ff6b35, #f7931e); color: #f9f6f2; font-size: 18px; animation: glow 2s infinite; }
    .tile-8192 { background: linear-gradient(135deg, #f7931e, #ffcc02); color: #f9f6f2; font-size: 18px; animation: glow 2s infinite; }
    .tile-0 { background: #cdc1b4; color: transparent; }
    
    .tile-new { animation: tileAppear 0.3s ease-out; }
    .tile-merge { animation: tileMerge 0.3s ease-out; }
    .tile-move { animation: tileMove 0.3s ease-out; }
    .board-shake { animation: boardShake 0.5s ease-in-out; }
    
    .score-container {
        background: linear-gradient(135deg, #eee, #f5f5f5);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 2px solid #ddd;
    }
    
    .score-label {
        font-size: 18px;
        font-weight: 700;
        color: #776e65;
        margin-bottom: 5px;
    }
    
    .score-value {
        font-size: 24px;
        font-weight: 900;
        color: #f65e3b;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .score-popup {
        position: absolute;
        font-weight: 700;
        color: #f65e3b;
        pointer-events: none;
        animation: scorePopup 1s ease-out forwards;
    }
    
    .controls-container {
        background: linear-gradient(135deg, #f8f8f8, #e8e8e8);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }
    
    .move-button {
        background: linear-gradient(135deg, #8f7a66, #9f8a76);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        width: 100%;
        margin: 5px 0;
    }
    
    .move-button:hover {
        background: linear-gradient(135deg, #9f8a76, #af9a86);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
    }
    
    .move-button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .restart-button {
        background: linear-gradient(135deg, #f65e3b, #edcf72);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 18px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 6px 15px rgba(246, 94, 59, 0.3);
        width: 100%;
        margin-top: 15px;
    }
    
    .restart-button:hover {
        background: linear-gradient(135deg, #edcf72, #f65e3b);
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(246, 94, 59, 0.4);
    }
    
    .game-title {
        background: linear-gradient(135deg, #8f7a66, #f65e3b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .game-title {
            font-size: 2rem;
        }
        
        .tile {
            width: 70px;
            height: 70px;
            font-size: 20px !important;
        }
        
        .tile-2, .tile-4, .tile-8 { font-size: 20px !important; }
        .tile-16, .tile-32, .tile-64 { font-size: 18px !important; }
        .tile-128, .tile-256, .tile-512 { font-size: 16px !important; }
        .tile-1024 { font-size: 14px !important; }
        .tile-2048, .tile-4096, .tile-8192 { font-size: 12px !important; }
        
        .game-board {
            padding: 10px;
        }
        
        .board-row {
            gap: 8px;
            margin-bottom: 8px;
        }
        
        .controls-container {
            padding: 15px;
        }
        
        .move-button {
            padding: 10px 16px;
            font-size: 14px;
        }
        
        .restart-button {
            padding: 12px 24px;
            font-size: 16px;
        }
    }
    
    @media (max-width: 480px) {
        .tile {
            width: 60px;
            height: 60px;
            font-size: 16px !important;
        }
        
        .tile-2, .tile-4, .tile-8 { font-size: 16px !important; }
        .tile-16, .tile-32, .tile-64 { font-size: 14px !important; }
        .tile-128, .tile-256, .tile-512 { font-size: 12px !important; }
        .tile-1024 { font-size: 10px !important; }
        .tile-2048, .tile-4096, .tile-8192 { font-size: 9px !important; }
        
        .game-board {
            padding: 8px;
        }
        
        .board-row {
            gap: 6px;
            margin-bottom: 6px;
        }
    }
    </style>
    """

def tile_style(val, is_new=False, is_merge=False):
    """Generate CSS class for tile styling"""
    if val == 0:
        return "tile tile-0"
    
    classes = [f"tile tile-{val}"]
    if is_new:
        classes.append("tile-new")
    if is_merge:
        classes.append("tile-merge")
    
    return " ".join(classes)


def render_board_html(board, score, score_gain=0):
    """Render the game board with enhanced graphics and animations"""
    html = f"""
    <div style='display:flex; align-items:flex-start; gap:30px; flex-wrap:wrap;'>
        <div class='game-board' id='gameBoard'>
    """
    
    # Render the board with enhanced styling
    for i in range(BOARD_SIZE):
        html += "<div class='board-row'>"
        for j in range(BOARD_SIZE):
            val = int(board[i, j])
            tile_class = tile_style(val)
            txt = str(val) if val != 0 else ""
            html += f"<div class='{tile_class}'>{txt}</div>"
        html += "</div>"
    
    html += """
        </div>
        
       
    </div>
    
    <script>
    // Enhanced interactive effects and particle system
    document.addEventListener('DOMContentLoaded', function() {
        const tiles = document.querySelectorAll('.tile:not(.tile-0)');
        const gameBoard = document.getElementById('gameBoard');
        
        // Enhanced tile hover effects
        tiles.forEach(tile => {
            tile.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.05) rotate(2deg)';
                this.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.4)';
                this.style.zIndex = '10';
                
                // Add sparkle effect
                createSparkle(this);
            });
            
            tile.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1) rotate(0deg)';
                this.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
                this.style.zIndex = '1';
            });
            
            // Add click effect
            tile.addEventListener('click', function() {
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 100);
            });
        });
        
        // Particle system for tile interactions
        function createSparkle(element) {
            const rect = element.getBoundingClientRect();
            const sparkle = document.createElement('div');
            sparkle.style.cssText = `
                position: fixed;
                width: 4px;
                height: 4px;
                background: radial-gradient(circle, #fff, transparent);
                border-radius: 50%;
                pointer-events: none;
                z-index: 1000;
                left: ${rect.left + Math.random() * rect.width}px;
                top: ${rect.top + Math.random() * rect.height}px;
                animation: sparkleAnim 1s ease-out forwards;
            `;
            
            document.body.appendChild(sparkle);
            setTimeout(() => sparkle.remove(), 1000);
        }
        
        // Add CSS for sparkle animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes sparkleAnim {
                0% { 
                    opacity: 1; 
                    transform: scale(0) rotate(0deg); 
                }
                50% { 
                    opacity: 1; 
                    transform: scale(1) rotate(180deg); 
                }
                100% { 
                    opacity: 0; 
                    transform: scale(0.5) rotate(360deg) translateY(-20px); 
                }
            }
            
            .tile-2048, .tile-4096, .tile-8192 {
                position: relative;
                overflow: visible;
            }
            
            .tile-2048::after, .tile-4096::after, .tile-8192::after {
                content: '✨';
                position: absolute;
                top: -10px;
                right: -10px;
                font-size: 16px;
                animation: float 2s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-5px); }
            }
        `;
        document.head.appendChild(style);
        
        // Add board shake effect
        if (gameBoard) {
            setTimeout(() => {
                gameBoard.classList.add('board-shake');
                setTimeout(() => {
                    gameBoard.classList.remove('board-shake');
                }, 500);
            }, 100);
        }
        
        // Add ripple effect on board click
        gameBoard.addEventListener('click', function(e) {
            const ripple = document.createElement('div');
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ripple.style.cssText = `
                position: absolute;
                width: 20px;
                height: 20px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                left: ${x - 10}px;
                top: ${y - 10}px;
                animation: ripple 0.6s ease-out forwards;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
        
        // Add ripple animation
        const rippleStyle = document.createElement('style');
        rippleStyle.textContent = `
            @keyframes ripple {
                0% { 
                    transform: scale(0); 
                    opacity: 1; 
                }
                100% { 
                    transform: scale(10); 
                    opacity: 0; 
                }
            }
        `;
        document.head.appendChild(rippleStyle);
        
        // Sound effects using Web Audio API
        let audioContext;
        
        function initAudio() {
            try {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            } catch (e) {
                console.log('Web Audio API not supported');
            }
        }
        
        function playSound(frequency, duration, type = 'sine') {
            if (!audioContext) return;
            
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
            oscillator.type = type;
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
        }
        
        // Sound effects for different actions
        function playMoveSound() {
            playSound(440, 0.1, 'square'); // A4 note
        }
        
        function playMergeSound() {
            playSound(523.25, 0.2, 'sawtooth'); // C5 note
        }
        
        function playNewTileSound() {
            playSound(659.25, 0.15, 'triangle'); // E5 note
        }
        
        function playWinSound() {
            // Play a little melody
            const melody = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
            melody.forEach((freq, index) => {
                setTimeout(() => playSound(freq, 0.3, 'sine'), index * 200);
            });
        }
        
        // Initialize audio on first user interaction
        document.addEventListener('click', initAudio, { once: true });
        document.addEventListener('touchstart', initAudio, { once: true });
        
        // Add sound to button clicks
        document.querySelectorAll('.move-button').forEach(button => {
            button.addEventListener('click', () => {
                setTimeout(playMoveSound, 100);
            });
        });
        
        // Enhanced keyboard controls with better button targeting
        document.addEventListener('keydown', function(e) {
            if (!audioContext) initAudio();
            
            // Prevent default arrow key behavior (page scrolling)
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                e.preventDefault();
            }
            
            let buttonClicked = false;
            
            switch(e.key) {
                case 'ArrowUp':
                case 'w':
                case 'W':
                    // Try multiple selectors to find the Up button
                    const upButton = Array.from(document.querySelectorAll('button')).find(btn => 
                        btn.textContent.includes('⬆️') || btn.textContent.includes('Up'));
                    if (upButton) {
                        upButton.click();
                        buttonClicked = true;
                        playMoveSound();
                    }
                    break;
                    
                case 'ArrowDown':
                case 's':
                case 'S':
                    const downButton = Array.from(document.querySelectorAll('button')).find(btn => 
                        btn.textContent.includes('⬇️') || btn.textContent.includes('Down'));
                    if (downButton) {
                        downButton.click();
                        buttonClicked = true;
                        playMoveSound();
                    }
                    break;
                    
                case 'ArrowLeft':
                case 'a':
                case 'A':
                    const leftButton = Array.from(document.querySelectorAll('button')).find(btn => 
                        btn.textContent.includes('⬅️') || btn.textContent.includes('Left'));
                    if (leftButton) {
                        leftButton.click();
                        buttonClicked = true;
                        playMoveSound();
                    }
                    break;
                    
                case 'ArrowRight':
                case 'd':
                case 'D':
                    const rightButton = Array.from(document.querySelectorAll('button')).find(btn => 
                        btn.textContent.includes('➡️') || btn.textContent.includes('Right'));
                    if (rightButton) {
                        rightButton.click();
                        buttonClicked = true;
                        playMoveSound();
                    }
                    break;
                    
                case 'r':
                case 'R':
                    const restartButton = Array.from(document.querySelectorAll('button')).find(btn => 
                        btn.textContent.includes('🔄') || btn.textContent.includes('New Game'));
                    if (restartButton) {
                        restartButton.click();
                        buttonClicked = true;
                    }
                    break;
                    
                case ' ': // Spacebar for restart
                    e.preventDefault();
                    const spaceRestartButton = Array.from(document.querySelectorAll('button')).find(btn => 
                        btn.textContent.includes('🔄') || btn.textContent.includes('New Game'));
                    if (spaceRestartButton) {
                        spaceRestartButton.click();
                        buttonClicked = true;
                    }
                    break;
            }
            
            // Visual feedback for successful key press
            if (buttonClicked && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                // Add a subtle visual indicator
                const indicator = document.createElement('div');
                indicator.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: rgba(246, 94, 59, 0.8);
                    color: white;
                    padding: 10px 20px;
                    border-radius: 25px;
                    font-weight: bold;
                    z-index: 1000;
                    pointer-events: none;
                    animation: keyPressIndicator 0.5s ease-out forwards;
                `;
                indicator.textContent = e.key.replace('Arrow', '');
                document.body.appendChild(indicator);
                
                setTimeout(() => indicator.remove(), 500);
            }
        });
        
        // Add CSS for key press indicator
        const keyIndicatorStyle = document.createElement('style');
        keyIndicatorStyle.textContent = `
            @keyframes keyPressIndicator {
                0% { 
                    opacity: 0; 
                    transform: translate(-50%, -50%) scale(0.5); 
                }
                50% { 
                    opacity: 1; 
                    transform: translate(-50%, -50%) scale(1.1); 
                }
                100% { 
                    opacity: 0; 
                    transform: translate(-50%, -50%) scale(1); 
                }
            }
        `;
        document.head.appendChild(keyIndicatorStyle);
        
        // Add keyboard hint
        const keyboardHint = document.createElement('div');
        keyboardHint.innerHTML = `
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
                font-size: 12px;
                z-index: 1000;
                opacity: 0.8;
                transition: opacity 0.3s ease;
            " onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.8'">
                🎮 Arrow Keys or WASD to Play
            </div>
        `;
        document.body.appendChild(keyboardHint);
        
        // Hide keyboard hint after 5 seconds
        setTimeout(() => {
            if (keyboardHint) {
                keyboardHint.style.opacity = '0';
                setTimeout(() => keyboardHint.remove(), 300);
            }
        }, 5000);
    });
    </script>
    """
    
    return html


# --- Streamlit app ---

def init_session():
    if "board" not in st.session_state:
        st.session_state.board = new_board()
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "game_over" not in st.session_state:
        st.session_state.game_over = False
    if "won" not in st.session_state:
        st.session_state.won = False
    if "score_gain" not in st.session_state:
        st.session_state.score_gain = 0
    if "last_move_time" not in st.session_state:
        st.session_state.last_move_time = 0


st.set_page_config(page_title="🎮 2048 Enhanced", layout="centered", page_icon="🎮")

# Inject CSS styles
st.markdown(get_css_styles(), unsafe_allow_html=True)

# Enhanced title
st.markdown('<h1 class="game-title">🎮 2048 Enhanced</h1>', unsafe_allow_html=True)

init_session()

col1, col2 = st.columns([3, 1])
with col1:
    # Enhanced instructions
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 4px solid #f65e3b;'>
        <h3 style='color: #8f7a66; margin-top: 0;'>🎯 How to Play</h3>
        <ul style='color: #776e65; margin-bottom: 0;'>
            <li>Use the arrow buttons below to slide tiles in any direction</li>
            <li>Combine tiles with the same number to merge them</li>
            <li>Reach <strong>2048</strong> to win! 🏆</li>
            <li>Keep going for higher scores and bigger tiles</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Render enhanced board
    board_html = render_board_html(st.session_state.board, st.session_state.score, st.session_state.score_gain)
    st.markdown(board_html, unsafe_allow_html=True)

    # Enhanced status messages
    if st.session_state.game_over:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #ff6b6b, #ee5a24); color: white; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0;'>
            <h3 style='margin: 0;'>💀 Game Over!</h3>
            <p style='margin: 10px 0 0 0;'>No moves left. Click Restart to try again!</p>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.won:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #00b894, #00a085); color: white; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0;'>
            <h3 style='margin: 0;'>🎉 Congratulations!</h3>
            <p style='margin: 10px 0 0 0;'>You reached 2048! Keep going for higher scores!</p>
        </div>
        """, unsafe_allow_html=True)

    # Enhanced controls
    st.markdown('<div class="controls-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #8f7a66; margin-bottom: 15px;">🎮 Controls</h3>', unsafe_allow_html=True)
    
    # Movement buttons in a more intuitive layout
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⬆️ Up", key="up", use_container_width=True):
            new_b, moved, gained = move_up(st.session_state.board)
            if moved:
                st.session_state.board = new_b
                st.session_state.score += gained
                st.session_state.score_gain = gained
                st.session_state.last_move_time = time.time()
                add_random_tile(st.session_state.board)
                st.rerun()
    with c2:
        if st.button("⬅️ Left", key="left", use_container_width=True):
            new_b, moved, gained = move_left(st.session_state.board)
            if moved:
                st.session_state.board = new_b
                st.session_state.score += gained
                st.session_state.score_gain = gained
                st.session_state.last_move_time = time.time()
                add_random_tile(st.session_state.board)
                st.rerun()
    with c3:
        if st.button("➡️ Right", key="right", use_container_width=True):
            new_b, moved, gained = move_right(st.session_state.board)
            if moved:
                st.session_state.board = new_b
                st.session_state.score += gained
                st.session_state.score_gain = gained
                st.session_state.last_move_time = time.time()
                add_random_tile(st.session_state.board)
                st.rerun()

    c4, c5, c6 = st.columns(3)
    with c2:
        if st.button("⬇️ Down", key="down", use_container_width=True):
            new_b, moved, gained = move_down(st.session_state.board)
            if moved:
                st.session_state.board = new_b
                st.session_state.score += gained
                st.session_state.score_gain = gained
                st.session_state.last_move_time = time.time()
                add_random_tile(st.session_state.board)
                st.rerun()

    # Clear score gain after a short delay
    if time.time() - st.session_state.last_move_time > 1:
        st.session_state.score_gain = 0

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced restart button
    if st.button("🔄 New Game", use_container_width=True):
        st.session_state.board = new_board()
        st.session_state.score = 0
        st.session_state.game_over = False
        st.session_state.won = False
        st.session_state.score_gain = 0
        st.rerun()

with col2:
    # Enhanced sidebar
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
        <h3 style='color: #8f7a66; margin-top: 0;'>🎯 Game Stats</h3>
        <div style='text-align: center;'>
            <div style='font-size: 24px; font-weight: 700; color: #f65e3b;'>""" + str(st.session_state.score) + """</div>
            <div style='color: #776e65;'>Current Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #e8f4fd, #d1ecf1); padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
        <h3 style='color: #8f7a66; margin-top: 0;'>💡 Pro Tips</h3>
        <ul style='color: #776e65; margin-bottom: 0; font-size: 14px;'>
            <li><strong>Corner Strategy:</strong> Keep your largest tile in a corner</li>
            <li><strong>Edge Control:</strong> Build along one edge, not the center</li>
            <li><strong>Think Ahead:</strong> Plan 2-3 moves ahead</li>
            <li><strong>Don't Merge:</strong> Avoid merging unless necessary</li>
            <li><strong>Stay Focused:</strong> One direction at a time works best</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #fff3cd, #ffeaa7); padding: 20px; border-radius: 12px;'>
        <h3 style='color: #8f7a66; margin-top: 0;'>🎮 Controls</h3>
        <p style='color: #776e65; margin-bottom: 10px; font-size: 14px;'>Use the arrow buttons to move tiles in any direction.</p>
        <p style='color: #776e65; margin-bottom: 0; font-size: 12px;'>💡 <em>Tip: Try using keyboard arrow keys if available!</em></p>
    </div>
    """, unsafe_allow_html=True)

# Check for win or game over after any action
if np.any(st.session_state.board == 2048):
    st.session_state.won = True

if not can_move(st.session_state.board):
    st.session_state.game_over = True
