# Documentation/build corrections
The first documentation script requested standalone wheel package metadata, but bdist_wheel was supplied by setuptools. That metadata lookup failed after text edits. A re-run also found its old text anchor already replaced. Environment recording was corrected separately; the generated wheel was rebuilt. No model parameters or datasets changed.
