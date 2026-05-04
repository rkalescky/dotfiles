ANSIBLE_ENV = ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp
ANSIBLE_INVENTORY = inventory/localhost.yml
EXTRA_ARGS ?=

.PHONY: bootstrap lima-vms

bootstrap:
	$(ANSIBLE_ENV) ansible-playbook -i $(ANSIBLE_INVENTORY) bootstrap.yml

lima-vms:
	$(ANSIBLE_ENV) ansible-playbook -i $(ANSIBLE_INVENTORY) playbooks/lima_vms.yml $(EXTRA_ARGS)
