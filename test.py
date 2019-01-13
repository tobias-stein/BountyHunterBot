from BountyHunter import Game

game = Game(2, 1)
game.Restart()

for i in range(500):
    print("" if game.Step() < 0 else "Game Over!")
    print(f"\nFrame: #{i}")
    game.DumpGameState()
    game.RenderGameState()

game.Terminate()
