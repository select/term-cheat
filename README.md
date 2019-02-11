# TermCheat: your terminal cheat sheet

## Synopsis

TermCheat is a searchable library of commands that you can copy remix and extend 

![Imgur Image](https://i.imgur.com/smJ3gWu.png)

## Usage

```bash
term-cheat
```

Even better if you add a keyboard shortcut to start TermCheat e.g. <kbd>Ctrl</kbd><kbd>a</kbd> 

Add this to your `.bashrc` or `.zshrc`  or ...

```
bindkey -s '^A' 'term-cheat --filter^M'
```

- `-s` simulate keyboard input
- `^A` <kbd>Ctrl</kbd><kbd>a</kbd>
- `^M` <kbd>Enter</kbd> key to run the command

## Keyboard Shortcuts

In *list* mode
- <kbd>enter</kbd> execute command
- <kbd>/</kbd> to fuzzy filter / search for a command 
- <kbd>a</kbd> add new command
- <kbd>e</kbd> edit selected command
- <kbd>d</kbd> delected the selected command


In *edit* mode
- <kbd>esc</kbd> to leave edit mode without saving
- <kbd>ctrl o</kbd> to save the command to your database

In *filter* mode
- <kbd>esc</kbd> to clear the filter

## Installation

While the package is waiting for approval from the snap store you can install it by downloading it from here and installing it with snap. 
```
curl -OL https://github.com/select/term-cheat/releases/download/0.1.11/term-cheat-0.1.11_amd64.snap
sudo snap install --classic --dangerous term-cheat-0.1.11_amd64.snap
```
So far I only tested it with Ubuntu 18.10.

<!-- Install the snap package (hopefully soon)
```bash
snap install term-cheat
```
 -->

To install it from source do the following.
```bash
git clone https://github.com/select/term-cheat.git
cd term-cheat
pipenv install
pipenv shell
python3 termcheat
```

## Related Tools and Projects

**Reveser History Search**\
Search through your shell history with <kbd>Ctrl</kbd><kbd>R</kbd>

**Alias** \
Create a file that contains aliases for your most used commands. 
Create a the aliases file with `touch ~/.aliases` and add some aliases like
```
alias lt='ls -ltr'
alias df='pydf -h -B'
```
now source the file in your `.bashrc` or `.zshrc` 
```
source $HOME/.aliases
```
You could write all aliases directly in you rc file but this way it's more portable if you switch from e.g. bash to zsh.

Another trick is to sort your history for the commands you use the most and created aliases for these commands to save you time. Here is a command to get your top ten most used commands:
```
history | awk '{CMD[$2]++;count++;}END { for (a in CMD)print CMD[a] " " CMD[a]/count*100 "% " a;}' | grep -v "./" | column -c3 -s " " -t | sort -nr | nl |  head -n10
```

**Autosuggestions** \
If you are using zsh there is a neat plugin called [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions) which will automatically show you suggestions of commands you used before that you can complete using the right arrow key.

**More Related Projects** \

- [tldr](https://github.com/tldr-pages/tldr)
- [bropages](http://bropages.org/)
- [eg](https://github.com/srsudar/eg)
- [cheat](https://github.com/cheat/cheat) 

If you got other suggestions I would love to include them here.


## Motivation

There are two reasons why I created TermCheat. First of all I love using the terminal and lately I have been learning more things like systemd and just could not remember all the commands on the first go. While I use the [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions) plugin and reverse history search (<kbd>ctrl</kbd><kbd>r</kbd>) I still had sometimes problems to recall commands. Furthermore both of these options to not give any additional information about the commands. Most modern editors (sublime-text, atom, ...) now have the option to search for commands with ctrl p which I find super helpful. 

The second reason which is even more important for me is that I find text base user interface (tui) very cool. They give you a proper hacker feeling and if done right are beautiful and fast. I wanted to challenge myself and see if I could build such an interface, and voila two weekends later I had the first version of TermCheat running. After working many years on web based interfaces building a tui is a really nice experience because it's pure minimalism.

## License

TermCheat is released under the [MIT License](http://termcheat.mit-license.org/).
