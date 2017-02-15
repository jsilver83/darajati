Deployment Instructions
=======================

Requirements
------------

1. Ansible version 2.1 or later.

    To get a recent version of Ansible on Debian stable, add the backports
    repository. For more details, see
    https://backports.debian.org/Instructions/.

2. Vault.

    Vault is available for all platforms as a statically linked binary at
    https://www.vaultproject.io/downloads.html.

    No installation is required. Just download and extract the zip file
    anywhere. To use the extracted file, either run it using its absolute path
    or add it to your `PATH` environment variable.

    The rest of this document assumes that the `vault` binary is in your path.


Create the Secrets in Vault
---------------------------

1. Authenticate to Vault:

        $ VAULT_SKIP_VERIFY=1 VAULT_ADDR="https://vault-1.test.kfupm.edu.sa:8200" vault auth -method=ldap username=<your-AD-username>

2. Generate the application's secret key by running the following one-liner in a
   Python 3 shell:

        import random, string; SECRET_KEY = ''.join([random.SystemRandom().choice("{}{}{}".format(string.ascii_letters, string.digits, string.punctuation)) for i in range(50)]); print(SECRET_KEY)

    Example:

        $ python3
		Type "help", "copyright", "credits" or "license" for more information.
	    >>> import random, string; SECRET_KEY = ''.join([random.SystemRandom().choice("{}{}{}".format(string.ascii_letters, string.digits, string.punctuation)) for i in range(50)]); print(SECRET_KEY)

    A valid secret key will be printed. We will use this key in the following
    step. To avoid having to escape any characters, avoid keys that contain the
    backslash character (`\`). You can re-run the command above to obtain
    different keys.

3. Write the secret key to Vault:

	    VAULT_SKIP_VERIFY=1 VAULT_ADDR="https://vault-1.test.kfupm.edu.sa:8200" vault write secret/testing/apps/darajati/secret_key value=<generated-secret-key>

    where `<generated-secret-key>` is the key you generated in the previous step.

4. Generate and write a new random database password to Vault.

    Use https://www.grc.com/passwords.htm to generate secure passwords (use the
    second or third red random string boxes; do not use the first!).

        $ VAULT_SKIP_VERIFY=1 VAULT_ADDR="https://vault-1.test.kfupm.edu.sa:8200" vault write secret/testing/apps/darajati/database_password value=<generated-database-password>

5. Generate and write a new email password to Vault.

	    $ VAULT_SKIP_VERIFY=1 VAULT_ADDR="https://vault-1.test.kfupm.edu.sa:8200" vault write secret/testing/apps/darajati/email_password value=<generated-email-password>

6. Change the email password of the application email user: log into
   https://mail.kfupm.edu.sa/ using the application user, e.g. `darajati@kfupm.edu.sa`, and change the password to the
   password generated and written to Vault in the previous step.


Application Deployment
----------------------

1. Change to this directory (`darajati/deploy`):

        cd deploy

2. Install the required Ansible roles.

        $ ansible-galaxy install -f -r requirements.yml

    This is almost always required. However, it is not required if you are not
    using any pre-defined roles, or if you have the `ansible-roles` repository
    at `../../config` relative to the root of this repository.

    You will need to execute this command every time your application upgrades
    the version it is using of any of its dependency roles, in order to get the
    current version of the role.

    If you run into an issue where https://vault-1.test.kfupm.edu.sa:8200 is not
    responding, then edit the files `application.yml` and `database.yml`, and
    replace Change the lines with https://vault-1.test.kfupm.edu.sa:8200 with
    https://vault-2.test.kfupm.edu.sa:8200

3. Create the application database by running the database playbook:

	    ansible-playbook -i environments/testing/inventory database.yml

4. Configure access to the source code repository from the target server, to
   allow for deploying the code from the code repository to the target server.

    To do that, edit the SSH configuration file on your local machine
    (`$HOME/.ssh/config`), and add the following two lines to it:

        host apps-*.test.kfupm.edu.sa
            ForwardAgent yes

    This change should be performed on the machine from which you are running
    the deployment command listed in the following step.

    These two lines will forward your SSH agent to the target machine, allowing
    the deployment command to employ your authorization to access the source
    code repository. Therefore, this will automatically allow you to only deploy
    from repositories you are authorized to access.

5. Deploy the applications:

        ansible-playbook -i environments/testing/inventory application.yml


6. (Optional) Create a Django superuser.

    - To create a Django superuser without a password, e.g. when using CAS
      authentication:

            ansible-playbook -i environments/testing/inventory application.yml -e django_project_create_admin_user=yes

    - To create a Django superuser with a password:

            ansible-playbook -i environments/testing/inventory application.yml -e django_project_admin_password='<the-password>'
