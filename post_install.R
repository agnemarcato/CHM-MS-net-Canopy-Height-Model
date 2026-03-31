options(repos = c(CRAN = "https://cloud.r-project.org"))
Sys.setenv(R_REMOTES_STANDALONE = "true")

message("=== Installer packages ===")
if (!requireNamespace("remotes", quietly = TRUE)) {
  install.packages("remotes")
}

install_github_checked <- function(repo, pkg = sub(".*/", "", repo), dependencies = FALSE) {
  message(sprintf("=== Installing %s from %s ===", pkg, repo))

  ok <- tryCatch({
    remotes::install_github(
      repo,
      upgrade = "never",
      dependencies = dependencies
    )
    TRUE
  }, error = function(e) {
    message(sprintf("FAILED during install: %s", pkg))
    message(conditionMessage(e))
    FALSE
  })

  installed <- requireNamespace(pkg, quietly = TRUE)

  if (ok && installed) {
    message(sprintf("SUCCESS: %s", pkg))
  } else if (!installed) {
    message(sprintf("NOT INSTALLED: %s", pkg))
  }

  invisible(installed)
}

message("=== Known good package ===")
if (!requireNamespace("lutz", quietly = TRUE)) {
  install.packages("lutz")
}
message(sprintf("lutz installed: %s", requireNamespace("lutz", quietly = TRUE)))

message("=== GitHub installs ===")
install_github_checked("tiagodc/TreeLS", "TreeLS")
install_github_checked("DRAAlmeida/leafR", "leafR")
install_github_checked("olgaviedma/LadderFuelsR", "LadderFuelsR")


# As of 3/31/26, the below installation is faling
message("=== cloud2trees ===")
install_github_checked(
  "georgewoolsey/cloud2trees",
  "cloud2trees",
  dependencies = TRUE
)

message("=== Final status ===")
pkgs <- c("lutz", "lasR", "TreeLS", "leafR", "LadderFuelsR", "cloud2trees")
status <- sapply(pkgs, requireNamespace, quietly = TRUE)
print(status)