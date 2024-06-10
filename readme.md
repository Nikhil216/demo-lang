## Title

Demo - A better modelling language for job scheduling optimization problem

## Introduction

In a attempt to write a better modelling language for job scheduling optimization problem. This language is not even a prototype. Thus, I'd like to call it just a demonstration. Due to lack of creativity, the modelling langauge will be named `demo`, short for demonstration.

## Design Goals

Demo is not trying to be flexible or comprehensive. As a result some job scheduling problem may not be expressed in demo. The primary goal is reduce the boilerplate required to write using the `python-mip` package.

## Tasks

- [x] Add scoping
- [x] let locals be handleded by scoping
- [x] Check for existing variables in `iden_table`
- [x] better model for scoping