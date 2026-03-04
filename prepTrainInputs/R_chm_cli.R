# © 2026. Triad National Security, LLC. All rights reserved.
# This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare. derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.


#!/usr/bin/env Rscript
# Lightweight wrapper to call chm_create() safely from Python without docopt

suppressPackageStartupMessages({
  library(jsonlite)
})

# Source your full utilities (docopt never runs because we don't call it)
source("Rutils.R")

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 1) {
  stop("Usage: R_chm_cli.R chm_create --las <file> --epsg <code> [--outdir <dir>]")
}

cmd <- args[1]

if (cmd == "chm_create") {
  las  <- args[which(args == "--las") + 1]
  epsg <- as.integer(args[which(args == "--epsg") + 1])
  outd <- if ("--outdir" %in% args) args[which(args == "--outdir") + 1] else "data"

  if (!dir.exists(outd)) dir.create(outd, recursive = TRUE, showWarnings = FALSE)

  msg <- chm_create(las, epsg, outd)
  cat(jsonlite::toJSON(list(ok = TRUE, message = msg), auto_unbox = TRUE))
  quit(status = 0)
}

stop("Unknown command: ", cmd)
