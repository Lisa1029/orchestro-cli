# Orchestro CLI - Documentation Test Demo

This is a sample documentation file to demonstrate the `orchestro doctest` command.

## Basic Shell Commands

You can test basic shell commands with expected output:

```bash
$ echo "Hello, Orchestro!"
Hello, Orchestro!

$ pwd
/home/jonbrookings/vibe_coding_projects/my-orchestro-copy
```

## Inline Expectations

For simple one-line outputs, you can use inline expectations with the `#=>` syntax:

```bash
$ echo "quick test"  #=> quick test

$ expr 2 + 2  #=> 4
```

## Commands Without Output Expectations

Some commands just need to succeed without specific output validation:

```bash
$ true

$ echo "This output won't be validated"
```

## Real CLI Commands

Test actual orchestro commands:

```bash
$ python -m orchestro_cli.cli --version  #=> 0.2.1
```

## Multi-line Output

You can test commands with multi-line output:

```bash
$ echo -e "Line 1\nLine 2\nLine 3"
Line 1
Line 2
Line 3
```

## Comments in Code Blocks

Comments are ignored during testing:

```bash
# This is a comment explaining the command
$ echo "test with comments"
test with comments

# Another comment
```

## Python Code (Not Tested)

Other language code blocks are not executed:

```python
print("This won't run")
```

Only shell/bash blocks are tested!
