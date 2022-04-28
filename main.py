from app import Window

# Adjust width / height (default window size)
WIDTH = 1080
HEIGHT = 720


# Main function definition
def main():
    app = Window(WIDTH,HEIGHT)    
    app.mainloop()
     
if __name__ == '__main__':
    main()
