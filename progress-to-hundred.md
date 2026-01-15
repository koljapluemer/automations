1. search in Obsidian vault (recursive) for all files where filename starts with `◩`
2. within these files, count top-level bullet points beginning with a date, which means a line beginning *exactly*:

```
- *yy-mm-dd
```

for example:
```
- *26-01-05
``` 

3. for each of these, generate a "progress bar" on the dashboard

- should be positioned in its own column to the right of all existing stuff, spanning the existing with
- simple layout with title of progress bar (= file basename), below it the progress bar, next
- the progress bar should count date entries and goes up to a hundred
- however, it should actually be made out of multiple blocks of different colors (find a nice, non-jarring palette):
    - first, one block representing the number of entries older than one week
    - then one block represnenting the number of entries in this calendar week (if any exist)
    - then one block representing the number of entries (0 or 1) today
    - (then the remaining space until 100 overall entries)