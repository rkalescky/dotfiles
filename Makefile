ANSIBLE_ENV = ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp
EXTRA_ARGS ?=

.PHONY: bootstrap lima-vms

bootstrap:
	$(ANSIBLE_ENV) ansible-playbook bootstrap.yml

lima-vms:
	$(ANSIBLE_ENV) ansible-playbook playbooks/lima_vms.yml $(EXTRA_ARGS)
