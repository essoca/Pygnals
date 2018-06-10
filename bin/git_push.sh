#!/bin/bash
git add .
read -p "Enter git comment: " cm
git commit -m "$cm"
git push -u origin master
