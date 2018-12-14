from BountyHunter import Game

game = Game(2)
game.Restart()

for i in range(500):
    game.Step()
    print(f"\nFrame: #{i}")
    game.DumpGameState()
    game.RenderGameState()

game.Terminate()
